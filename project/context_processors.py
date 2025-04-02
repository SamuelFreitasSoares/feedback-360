from .models import Avaliacao
from .utils import obter_notificacoes_usuario

def user_data(request):
    """
    Adiciona dados do usuário ao contexto de todos os templates
    """
    context = {
        'user_type': request.session.get('user_type'),
        'user_id': request.session.get('user_id'),
        'username': request.session.get('username'),
    }
    
    # Adicionar notificações não lidas
    if 'user_type' in request.session:
        notificacoes = obter_notificacoes_usuario(request)
        context['notificacoes_nao_lidas'] = notificacoes.filter(lida=False)
        context['notificacoes_count'] = context['notificacoes_nao_lidas'].count()
    
    return context
