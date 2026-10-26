import os

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    RunContext,
    function_tool,
)
from livekit.plugins import openai
from openai.types.beta.realtime.session import TurnDetection

import backend

load_dotenv(".env.local")
load_dotenv()

TURN_DETECTION = TurnDetection(
    type="server_vad",
    threshold=0.6,
    prefix_padding_ms=300,
    silence_duration_ms=700,
    create_response=True,
    interrupt_response=True,
)

INSTRUCOES = """
Você é a Ana, atendente virtual da Central de Cobrança da Empresa Exemplo.
Fale português do Brasil, em frases curtas e naturais, como em uma ligação.
Não use listas, markdown, emojis ou símbolos.

Regras:
1. Só revele qualquer informação sobre a dívida depois de confirmar CPF e data de nascimento com a tool consultar_divida.
2. Nunca invente valores, parcelas, vencimentos ou descontos. Use somente o retorno das tools.
3. Ao apresentar o valor e um plano, faça o cliente confirmar explicitamente antes de criar o acordo.
4. Só chame criar_acordo depois da confirmação do cliente.
5. Se o cliente contestar a dívida, pedir atendimento humano ou relatar dificuldade, chame transferir_para_humano.
6. Seja respeitosa. Não ameace, não constranja e não mencione outras pessoas.
7. Se o cliente não souber o CPF ou a data de nascimento, oriente e pergunte novamente.
"""


class CobrancaAgent(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=INSTRUCOES)

    @function_tool()
    async def consultar_divida(
        self,
        context: RunContext,
        cpf: str,
        data_nascimento: str,
    ) -> dict:
        """Consulta a dívida do cliente. Use somente depois de obter CPF e data de nascimento.

        Args:
            cpf: CPF do cliente, com ou sem pontuação.
            data_nascimento: Data de nascimento no formato DD/MM/AAAA.
        """
        return await backend.consultar_divida(cpf, data_nascimento)

    @function_tool()
    async def listar_planos(self, context: RunContext, cpf: str) -> dict:
        """Lista os planos de pagamento disponíveis para o CPF já verificado.

        Args:
            cpf: CPF do cliente já verificado.
        """
        return await backend.listar_planos(cpf)

    @function_tool()
    async def criar_acordo(
        self,
        context: RunContext,
        cpf: str,
        plano_id: str,
    ) -> dict:
        """Cria o acordo depois que o cliente confirmar explicitamente o plano e o valor.

        Args:
            cpf: CPF do cliente já verificado.
            plano_id: ID do plano confirmado: a_vista, 3x, 6x ou 12x.
        """
        context.disallow_interruptions()
        return await backend.criar_acordo(cpf, plano_id)

    @function_tool()
    async def transferir_para_humano(self, context: RunContext, motivo: str) -> dict:
        """Transfere o atendimento para um humano.

        Args:
            motivo: Motivo da transferência.
        """
        return await backend.transferir_para_humano(motivo)


server = AgentServer()


@server.rtc_session(agent_name="cobranca")
async def cobranca(ctx: JobContext):
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(
            model=os.getenv("OPENAI_REALTIME_MODEL", "gpt-realtime-2.1"),
            voice=os.getenv("OPENAI_VOICE", "marin"),
            input_audio_noise_reduction="near_field",
            turn_detection=TURN_DETECTION,
        ),
    )

    await session.start(room=ctx.room, agent=CobrancaAgent())
    await session.generate_reply(
        instructions=(
            "Cumprimente o cliente, diga que é a Ana da Central de Cobrança "
            "da Empresa Exemplo e peça o CPF e a data de nascimento para "
            "confirmar a identidade."
        )
    )


if __name__ == "__main__":
    agents.cli.run_app(server)
