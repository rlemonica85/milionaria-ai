"""CLI principal para pipeline completo da +Milionária."""

import argparse
import sys
import os
import time
from pathlib import Path

# Adicionar src ao path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from etl.from_db import load_draws
from features.make import build_number_features, latest_feature_snapshot
from models.scoring import learn_weights_ridge, score_numbers
from generate.tickets import generate_candidates, apply_filters, assign_trevos, load_filters_config
from simulate.backtest_ray import run_backtest_parallel, print_backtest_summary
from generate.export import export_excel


def run_pipeline(db_path: str = "db/milionaria.db",
                config_path: str = "configs/filters.yaml",
                seed: int = 42,
                n_show: int = 10,
                verbose: bool = True,
                export_path: str = None) -> list:
    """Executa pipeline completo da +Milionária.
    
    Args:
        db_path: Caminho para banco de dados
        config_path: Caminho para arquivo de configuração
        seed: Seed para reprodutibilidade
        n_show: Número de bilhetes para mostrar
        verbose: Se deve imprimir logs detalhados
        export_path: Caminho para exportar resultados em Excel (opcional)
        
    Returns:
        Lista de resultados do backtest ordenados por score
    """
    start_time = time.time()
    
    if verbose:
        print("🎯 === Pipeline +Milionária AI ===")
        print(f"📊 Configurações:")
        print(f"   - Database: {db_path}")
        print(f"   - Config: {config_path}")
        print(f"   - Seed: {seed}")
        print(f"   - Top bilhetes: {n_show}")
    
    # 1. Carregar dados do banco
    if verbose:
        print("\n📥 1. Carregando dados do banco...")
    
    try:
        df = load_draws(db_path)
        if verbose:
            print(f"   ✓ {len(df)} sorteios carregados")
    except Exception as e:
        print(f"   ❌ Erro ao carregar dados: {e}")
        return []
    
    # 2. Gerar features e aprender pesos
    if verbose:
        print("\n🧠 2. Gerando features e treinando modelo...")
    
    try:
        features = build_number_features(df)
        snapshot = latest_feature_snapshot(df)
        
        if verbose:
            print(f"   ✓ Features: {len(features)} amostras")
            print(f"   ✓ Snapshot: {len(snapshot)} números")
        
        model, scaler, weights = learn_weights_ridge(features)
        
        if verbose:
            print(f"   ✓ Modelo treinado")
            print(f"   ✓ Weights: {weights}")
            print(f"   ✓ Calculando scores...")
        
        scores = score_numbers(snapshot, weights)
        
        if verbose:
            print(f"   ✓ Scores calculados para {len(scores)} números")
    
    except Exception as e:
        print(f"   ❌ Erro no treinamento: {e}")
        return []
    
    # 3. Gerar candidatos e aplicar filtros
    if verbose:
        print("\n🎲 3. Gerando candidatos e aplicando filtros...")
    
    try:
        config = load_filters_config(config_path)
        
        # Gerar candidatos
        tickets = generate_candidates(
            scores,
            k=config['generation']['k'],
            top_pool=config['generation']['top_pool'],
            n=config['generation']['n'],
            seed=seed
        )
        
        if verbose:
            print(f"   ✓ {len(tickets)} candidatos gerados")
        
        # Aplicar filtros
        filtered_tickets = apply_filters(tickets, config['filters'])
        
        if verbose:
            print(f"   ✓ {len(filtered_tickets)} tickets após filtros ({len(filtered_tickets)/len(tickets)*100:.1f}% aprovação)")
        
        # Atribuir trevos
        top_tickets = filtered_tickets[:config['output']['top_k']]
        complete_tickets = assign_trevos(
            top_tickets,
            strategy=config['trevos']['strategy'],
            seed=seed
        )
        
        if verbose:
            print(f"   ✓ {len(complete_tickets)} bilhetes completos gerados")
    
    except Exception as e:
        print(f"   ❌ Erro na geração: {e}")
        return []
    
    # 4. Executar backtest
    if verbose:
        print("\n📈 4. Executando backtest paralelo...")
    
    try:
        results = run_backtest_parallel(
            complete_tickets, 
            df, 
            num_workers=4, 
            batch_size=max(1, len(complete_tickets) // 4)
        )
        
        if verbose:
            print(f"   ✓ Backtest concluído para {len(results)} bilhetes")
    
    except Exception as e:
        print(f"   ❌ Erro no backtest: {e}")
        return []
    
    # 5. Mostrar resultados
    if verbose:
        elapsed = time.time() - start_time
        print(f"\n⏱️  Pipeline concluído em {elapsed:.2f}s")
        
        print_backtest_summary(results, top_k=n_show)
        
        # Estatísticas adicionais
        if results:
            best_result = results[0]
            print(f"\n🏆 Melhor bilhete:")
            print(f"   Dezenas: {best_result['dezenas']}")
            print(f"   Trevos: {best_result['trevos']}")
            print(f"   Score: {best_result['score']:.4f}")
            print(f"   Acertos médios (dezenas): {best_result['avg_hits_dezenas']:.2f}")
            print(f"   Acertos médios (trevos): {best_result['avg_hits_trevos']:.2f}")
            print(f"   Máximo acertos (dezenas): {best_result['max_hits_dezenas']}")
            print(f"   Máximo acertos (trevos): {best_result['max_hits_trevos']}")
            
            if best_result['winning_draws']:
                print(f"   Sorteios com acertos: {len(best_result['winning_draws'])}")
                print(f"   Melhor sorteio: Concurso {best_result['winning_draws'][0]['concurso']} ({best_result['winning_draws'][0]['hits_dezenas']}+{best_result['winning_draws'][0]['hits_trevos']})")
    
    # 6. Exportar resultados se solicitado
    if export_path and results:
        if verbose:
            print(f"\n📄 6. Exportando resultados para {export_path}...")
        
        try:
            # Extrair apenas dezenas e trevos dos resultados do backtest
            tickets_for_export = []
            for result in results:
                dezenas = result['dezenas']
                trevos = result['trevos']
                tickets_for_export.append((dezenas, trevos))
            
            export_excel(tickets_for_export, export_path)
            if verbose:
                print(f"   ✓ Resultados exportados com sucesso")
        except Exception as e:
            if verbose:
                print(f"   ❌ Erro na exportação: {e}")
    
    return results


def main():
    """Função principal do CLI."""
    parser = argparse.ArgumentParser(
        description="Pipeline completo da +Milionária AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python -m src.cli.app                                    # Execução padrão
  python -m src.cli.app --seed 123 --n-show 5             # Seed personalizada, top 5
  python -m src.cli.app --cfg configs/aggressive.yaml     # Config alternativa
  python -m src.cli.app --db custom.db --n-show 20        # DB e top personalizados
        """
    )
    
    parser.add_argument(
        "--db",
        default="db/milionaria.db",
        help="Caminho para banco de dados (default: db/milionaria.db)"
    )
    
    parser.add_argument(
        "--cfg",
        default="configs/filters.yaml",
        help="Caminho para arquivo de configuração (default: configs/filters.yaml)"
    )
    
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed para reprodutibilidade (default: 42)"
    )
    
    parser.add_argument(
        "--n-show",
        type=int,
        default=10,
        help="Número de bilhetes para mostrar (default: 10)"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Modo silencioso (apenas resultados finais)"
    )
    
    parser.add_argument(
        "--export",
        type=str,
        help="Caminho para exportar resultados em Excel (ex: results.xlsx)"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="+Milionária AI Pipeline v1.0"
    )
    
    args = parser.parse_args()
    
    # Validar arquivos
    if not os.path.exists(args.db):
        print(f"❌ Erro: Banco de dados não encontrado: {args.db}")
        sys.exit(1)
    
    if not os.path.exists(args.cfg):
        print(f"❌ Erro: Arquivo de configuração não encontrado: {args.cfg}")
        sys.exit(1)
    
    # Executar pipeline
    try:
        results = run_pipeline(
            db_path=args.db,
            config_path=args.cfg,
            seed=args.seed,
            n_show=args.n_show,
            verbose=not args.quiet,
            export_path=args.export
        )
        
        if not results:
            print("❌ Pipeline falhou - nenhum resultado gerado")
            sys.exit(1)
        
        if args.quiet:
            # Modo silencioso - apenas top bilhetes
            print(f"Top {args.n_show} bilhetes:")
            for i, result in enumerate(results[:args.n_show]):
                print(f"{i+1:2d}. {result['dezenas']} + {result['trevos']} (score: {result['score']:.4f})")
        
        print("\n✅ Pipeline executado com sucesso!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Pipeline interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()