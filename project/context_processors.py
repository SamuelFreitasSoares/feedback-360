from .models import Avaliacao

def user_data(request):
    """
    Add user data to the context of all templates
    """
    context = {}
    
    if 'user_type' in request.session and 'user_id' in request.session:
        context['user_type'] = request.session.get('user_type')
        context['user_id'] = request.session.get('user_id')
        context['username'] = request.session.get('username', '')
        
        # Add pending evaluations count for students
        if context['user_type'] == 'aluno':
            pending_evaluations = Avaliacao.objects.filter(
                avaliador_aluno__idAluno=context['user_id'],
                concluida=False
            ).count()
            context['pending_evaluations'] = pending_evaluations
    
    return context
