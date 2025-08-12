# Sistema de Detecção de Anomalias

Este documento descreve o sistema implementado para detectar e notificar anomalias no processo de atualização automática da +Milionária.

## Funcionalidade

O sistema monitora execuções consecutivas do script `update_all.ps1` que não encontram novos concursos e dispara alertas quando um limite é atingido.

### Como Funciona

1. **Contador Persistente**: O arquivo `logs/no_new_draws_count.txt` mantém o contador de execuções consecutivas sem novos concursos
2. **Detecção de Anomalia**: Quando o contador atinge o limite configurado (padrão: 5), uma anomalia é detectada
3. **Notificação**: O sistema tenta enviar notificações via e-mail e/ou Telegram
4. **Código de Erro**: O script retorna código de erro 2 quando uma anomalia é detectada
5. **Reset Automático**: O contador é resetado quando novos concursos são encontrados

## Configuração

### 1. Variáveis de Ambiente

Copie o arquivo `.env.sample` para `.env` e configure as variáveis:

```bash
# E-mail
NOTIFY_EMAIL_ENABLED=true
NOTIFY_EMAIL_SMTP_HOST=smtp.gmail.com
NOTIFY_EMAIL_SMTP_PORT=587
NOTIFY_EMAIL_USERNAME=seu_email@gmail.com
NOTIFY_EMAIL_PASSWORD=sua_senha_app
NOTIFY_EMAIL_FROM=seu_email@gmail.com
NOTIFY_EMAIL_TO=destinatario@gmail.com

# Telegram
NOTIFY_TELEGRAM_ENABLED=true
NOTIFY_TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
NOTIFY_TELEGRAM_CHAT_ID=-1001234567890
```

### 2. Configuração do Limite

O limite de execuções consecutivas pode ser ajustado no script `tasks/update_all.ps1`:

```powershell
$MaxConsecutiveNoNewDraws = 5  # Altere conforme necessário
```

## Uso

### Execução Normal

```powershell
.\tasks\update_all.ps1
```

### Códigos de Retorno

- **0**: Sucesso, sem anomalias
- **1**: Erro durante execução
- **2**: Anomalia detectada (muitas execuções sem novos concursos)

### Teste do Sistema

Para testar o sistema de notificação:

```powershell
# Testar módulo de notificação
python -m src.utils.notify --type anomaly --message "Teste de anomalia"

# Simular condição de anomalia (modifique o contador manualmente)
echo "5" > logs\no_new_draws_count.txt
.\tasks\update_all.ps1
```

## Logs

### Exemplo de Log Normal

```
[2025-01-11 10:00:00] [INFO] Nenhum concurso novo encontrado
[2025-01-11 10:00:00] [INFO] Contador de execuções sem novos concursos: 3
```

### Exemplo de Log com Anomalia

```
[2025-01-11 10:00:00] [ERROR] ANOMALIA DETECTADA: 5 execuções consecutivas sem novos concursos (limite: 5)
[2025-01-11 10:00:00] [INFO] Tentando enviar notificação de anomalia...
[2025-01-11 10:00:01] [INFO] Notificação enviada: Notificação processada com sucesso
[2025-01-11 10:00:01] [ERROR] Retornando código de erro devido a anomalia detectada
```

## Arquivos Relacionados

- `tasks/update_all.ps1` - Script principal com lógica de detecção
- `src/utils/notify.py` - Módulo de notificação
- `.env.sample` - Exemplo de configuração
- `logs/no_new_draws_count.txt` - Contador persistente
- `logs/update_YYYYMMDD.log` - Logs diários de execução

## Troubleshooting

### Notificações Não Funcionam

1. Verifique se as variáveis de ambiente estão configuradas
2. Teste o módulo isoladamente: `python -m src.utils.notify --type info --message "Teste"`
3. Verifique os logs para mensagens de erro

### Contador Não Reseta

1. Verifique se o padrão de detecção de novos concursos está correto
2. Examine a saída do `update_db` nos logs
3. Verifique permissões de escrita no diretório `logs/`

### Falsos Positivos

1. Ajuste o limite `$MaxConsecutiveNoNewDraws` para um valor maior
2. Verifique se o padrão de detecção "Novos: 0" está correto
3. Considere adicionar mais condições de validação