from app.domain.entities import (
    Aluno,
    Badge,
    BadgeConquistada,
    Correcao,
    Missao,
    Professor,
    Submissao,
)
from app.domain.enums import PerfilUsuario
from app.infrastructure.database.models import (
    AlunoModel,
    BadgeConquistadaModel,
    BadgeModel,
    CorrecaoModel,
    MissaoModel,
    SubmissaoModel,
    UsuarioModel,
)


def usuario_model_para_aluno(model: AlunoModel) -> Aluno:
    usuario = model.usuario
    return Aluno(
        id=usuario.id,
        username=usuario.username,
        email=usuario.email,
        senha_hash=usuario.senha_hash,
        perfil=PerfilUsuario.ALUNO,
        nivel=model.nivel,
        xp_total=model.xp_total,
        xp_semana=model.xp_semana,
        dias_ofensiva=model.dias_ofensiva,
    )


def aluno_para_model(aluno: Aluno, usuario: UsuarioModel, aluno_model: AlunoModel) -> None:
    usuario.username = aluno.username
    usuario.email = aluno.email
    usuario.senha_hash = aluno.senha_hash
    aluno_model.nivel = aluno.nivel
    aluno_model.xp_total = aluno.xp_total
    aluno_model.xp_semana = aluno.xp_semana
    aluno_model.dias_ofensiva = aluno.dias_ofensiva


def missao_model_para_entidade(model: MissaoModel) -> Missao:
    return Missao(
        id=model.id,
        titulo=model.titulo,
        descricao=model.descricao,
        dificuldade=model.dificuldade,
        xp_recompensa=model.xp_recompensa,
        status=model.status,
        badge_id_recompensa=model.badge_id_recompensa,
        data_inicio=model.data_inicio,
        deadline=model.deadline,
        trilha_id=model.trilha_id,
        ordem=model.ordem,
    )


def missao_entidade_para_model(missao: Missao, model: MissaoModel) -> None:
    model.titulo = missao.titulo
    model.descricao = missao.descricao
    model.dificuldade = missao.dificuldade
    model.xp_recompensa = missao.xp_recompensa
    model.status = missao.status
    model.badge_id_recompensa = missao.badge_id_recompensa
    model.data_inicio = missao.data_inicio
    model.deadline = missao.deadline
    model.trilha_id = missao.trilha_id
    model.ordem = missao.ordem


def submissao_model_para_entidade(model: SubmissaoModel) -> Submissao:
    return Submissao(
        id=model.id,
        aluno_id=model.aluno_id,
        missao_id=model.missao_id,
        conteudo_codigo=model.conteudo_codigo,
        status=model.status,
        criado_em=model.criado_em,
        atualizado_em=model.atualizado_em,
    )


def submissao_entidade_para_model(submissao: Submissao, model: SubmissaoModel) -> None:
    model.conteudo_codigo = submissao.conteudo_codigo
    model.status = submissao.status
    model.atualizado_em = submissao.atualizado_em


def badge_model_para_entidade(model: BadgeModel) -> Badge:
    return Badge(
        id=model.id,
        codigo=model.codigo,
        nome=model.nome,
        descricao=model.descricao,
        icone_url=model.icone_url,
    )


def badge_conquistada_model_para_entidade(
    model: BadgeConquistadaModel,
) -> BadgeConquistada:
    return BadgeConquistada(
        aluno_id=model.aluno_id,
        badge_id=model.badge_id,
        conquistado_em=model.conquistado_em,
    )


def usuario_model_para_professor(model: UsuarioModel) -> Professor:
    return Professor(
        id=model.id,
        username=model.username,
        email=model.email,
        senha_hash=model.senha_hash,
        perfil=PerfilUsuario.PROFESSOR,
        departamento=model.departamento,
    )


def correcao_model_para_entidade(model: CorrecaoModel) -> Correcao:
    return Correcao(
        id=model.id,
        submissao_id=model.submissao_id,
        professor_id=model.professor_id,
        nota=model.nota,
        feedback=model.feedback,
        criado_em=model.criado_em,
    )
