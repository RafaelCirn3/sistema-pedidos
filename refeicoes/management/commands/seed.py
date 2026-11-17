import hashlib
import secrets
from io import BytesIO
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

from PIL import Image, ImageOps
from django.contrib.auth.models import Group, User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from refeicoes.models import Refeicao, OpcaoRefeicao
from usuarios.models import PerfilCliente


# Fotos ilustrativas de domínio público ou sob licença CC0 (ver README).
PRATOS = (
    ("Feijoada completa", "Feijão preto com carnes, arroz e farofa.", ("Couve", "Laranja", "Farofa extra"), "Brazilian food Feijoada.jpg"),
    ("Peixe grelhado", "Peixe acompanhado de arroz e feijão.", ("Salada", "Limão"), "Arroz, feijão e peixe grelhado.jpg"),
    ("Macarrão à bolonhesa", "Massa com molho de tomate e carne moída.", ("Queijo ralado", "Molho extra"), "Pastabolognese.jpg"),
    ("Omelete da casa", "Omelete preparado na hora.", ("Queijo", "Tomate", "Cebola"), "Eggs omelette.jpg"),
    ("Salada fresca", "Mix de folhas e legumes frescos.", ("Molho à parte", "Azeite"), "Salad On Plate.jpg"),
)


def baixar_foto(arquivo):
    # O caminho do Wikimedia Commons é determinado pelo MD5 do nome canônico.
    nome = arquivo.replace(" ", "_")
    digest = hashlib.md5(nome.encode("utf-8")).hexdigest()
    local = Path(__file__).resolve().parents[2] / "seed_images" / f"{digest}.jpg"
    if local.is_file():
        return ContentFile(local.read_bytes())
    url = f"https://upload.wikimedia.org/wikipedia/commons/{digest[0]}/{digest[:2]}/{quote(nome)}"
    request = Request(url, headers={"User-Agent": "MesaSistemaPedidos/1.0 (demo seed; https://github.com/RafaelCirn3/sistema-pedidos)"})
    limite = 16 * 1024 * 1024
    with urlopen(request, timeout=15) as resposta:
        dados = resposta.read(limite + 1)
    if len(dados) > limite:
        raise ValueError("Foto excede o limite de download.")
    with Image.open(BytesIO(dados)) as imagem:
        if imagem.format not in ("JPEG", "PNG", "WEBP"):
            raise ValueError("Formato de imagem inválido.")
        imagem = ImageOps.exif_transpose(imagem).convert("RGB")
        imagem.thumbnail((960, 960))
        buffer = BytesIO()
        imagem.save(buffer, format="JPEG", quality=85, optimize=True)
    return ContentFile(buffer.getvalue())


class Command(BaseCommand):
    help = "Cria usuários e pratos fictícios para demonstração. Não executar em produção."

    def add_arguments(self, parser):
        parser.add_argument("--sem-imagens", action="store_true", help="Não realiza downloads das fotos.")

    def handle(self, *args, **options):
        contas = (
            ("demo-admin", "admin.demo@example.test", "Administrador Demo", None),
            ("demo-cozinha", "cozinha.demo@example.test", "Cozinha Demo", "Cozinha"),
            ("cliente.demo@example.test", "cliente.demo@example.test", "Cliente Demo", "Cliente"),
        )
        credenciais = []
        with transaction.atomic():
            for username, email, nome, grupo in contas:
                existente = User.objects.filter(username=username).first()
                if existente:
                    # Não redefinir senha, perfil ou privilégios de usuários existentes.
                    self.stdout.write(f"Usuário {username} já existe; preservado.")
                    continue
                if User.objects.filter(email__iexact=email).exists():
                    raise CommandError(f"Já existe um usuário com o e-mail {email}.")
                senha = secrets.token_urlsafe(16)
                user = User.objects.create_user(username=username, email=email, first_name=nome, password=senha, is_staff=grupo is None, is_superuser=grupo is None)
                if grupo:
                    user.groups.add(Group.objects.get_or_create(name=grupo)[0])
                if grupo == "Cliente":
                    PerfilCliente.objects.create(usuario=user, whatsapp="+5583999990000")
                credenciais.append((username, senha))
        for username, senha in credenciais:
            self.stdout.write(self.style.SUCCESS(f"Usuário: {username} | Senha: {senha}"))

        falhas = []
        for nome, descricao, opcoes, arquivo in PRATOS:
            # Preservar dados editados pelo responsável e não recriar opções excluídas.
            with transaction.atomic():
                prato = Refeicao.objects.filter(nome=nome).order_by("pk").first()
                if prato is None:
                    prato = Refeicao.objects.create(nome=nome, descricao=descricao, disponivel=True)
                    OpcaoRefeicao.objects.bulk_create([OpcaoRefeicao(refeicao=prato, nome=opcao) for opcao in opcoes])
            if not options["sem_imagens"] and not prato.imagem:
                try:
                    foto = baixar_foto(arquivo)
                    prato.imagem.save("demo.jpg", foto)
                except (OSError, ValueError) as exc:
                    falhas.append(nome)
                    self.stderr.write(self.style.WARNING(f"Foto não baixada para {nome}: {exc}"))
            self.stdout.write(f"Prato: {nome}")
        if falhas:
            raise CommandError("Pratos cadastrados, mas faltam fotos. Execute o seed novamente com acesso à internet: " + ", ".join(falhas))
        self.stdout.write(self.style.SUCCESS("Seed concluído."))
