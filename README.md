# Agente de cobrança por voz (LiveKit + OpenAI Realtime)

Exemplo local, em Python/uv, de um agente de cobrança com fala e escuta em tempo real.
O LiveKit transporta o áudio, o OpenAI Realtime faz a conversa e as tools consultam
dados fictícios em `backend.py`.

## Estrutura

- `agent.py`: agente LiveKit, prompt e tools.
- `backend.py`: CPFs, dívidas, planos e acordos fictícios.
- `server.py`: token endpoint e servidor do front.
- `static/index.html`: front local mínimo para testar no navegador.
- `docker-compose.yml`: LiveKit local em modo de desenvolvimento.

## Requisitos

- Docker
- uv
- Chave da OpenAI

## Como rodar

1. Abra o `.env.local` já criado (ou rode `cp .env.example .env.local` se ele não existir)
   e preencha a chave da OpenAI:

```env
OPENAI_API_KEY=sk-...
```

Sem essa chave o agente até registra no LiveKit, mas a sessão de voz falha ao iniciar.
Se o modelo `gpt-realtime-2.1` não estiver disponível na sua conta, troque
`OPENAI_REALTIME_MODEL` para `gpt-realtime`.

2. Instale as dependências:

```bash
uv sync
```

3. Suba o LiveKit local:

```bash
docker compose up -d
```

4. Em um terminal, suba o agente:

```bash
uv run python agent.py dev
```

5. Em outro terminal, suba o front:

```bash
uv run python server.py
```

6. Abra <http://localhost:8000>, clique em **Iniciar conversa** e permita o microfone.
7. Segure o botão **Segurar para falar** enquanto fala e solte quando terminar.

Use fones para evitar eco. O LiveKit local usa `devkey`/`secret` apenas para teste.

Se o agente não for ouvido, clique em **Ativar áudio** (o navegador pode bloquear
a reprodução automática). A página também tem um player de áudio; se o log mostrar
`Áudio recebido de agent-...`, a track chegou e o problema é só reprodução/volume.
Se aparecerem transcrições sem sentido, o microfone está captando ruído ou o áudio
do próprio agente: use fones e fale apenas com o botão pressionado.

## CPFs fictícios

| CPF | Nome | Nascimento | Dívida |
| --- | --- | --- | --- |
| 111.111.111-11 | João da Silva | 01/01/1990 | R$ 1.584,56 |
| 222.222.222-22 | Maria Souza | 02/02/1985 | R$ 4.890,00 |
| 333.333.333-33 | Carlos Pereira | 03/03/2000 | Sem dívida |

Exemplo de conversa: informe o CPF e a data de nascimento, peça o valor, peça os planos,
escolha um plano e confirme. O agente só cria o acordo depois da confirmação.

## Teste rápido sem navegador

O LiveKit Agents também tem modo console:

```bash
uv run python agent.py console
```

Nesse modo o microfone e o alto-falante são do terminal, sem precisar subir o LiveKit.

## Sobre o front

Não usei Gradio porque ele não mantém uma sessão de áudio WebRTC full-duplex com
interrupção e turn-taking. Para o teste local, a página estática com o SDK da LiveKit é
mais simples e funciona de verdade. Se quiser, ela pode ser embutida em um iframe do
Gradio depois.

## Próximos passos

- Trocar os dados mockados de `backend.py` por uma API real.
- Adicionar confirmação de identidade mais forte e registro de auditoria.
- Adicionar transferência real para humano.
- Configurar SIP/Twilio/Telnyx no LiveKit para testar ligações telefônicas.
- Revisar LGPD, CDC art. 42, janela de cobrança e opt-out antes de uso real.
