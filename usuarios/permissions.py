from django.core.exceptions import PermissionDenied

def perfil(user):
    if user.is_superuser:
        return "admin"
    groups = set(user.groups.values_list("name", flat=True))
    if "Cozinha" in groups:
        return "cozinha"
    if "Cliente" in groups:
        return "cliente"
    raise PermissionDenied("Usuário sem perfil operacional.")

def exigir(user, *perfis):
    if perfil(user) not in perfis:
        raise PermissionDenied
