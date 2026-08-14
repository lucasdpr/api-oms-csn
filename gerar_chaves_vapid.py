# ==============================================================
# gerar_chaves_vapid.py
# ==============================================================
# Roda UMA VEZ pra gerar seu par de chaves VAPID (público/privado),
# necessário pro Web Push funcionar. Não tem custo nenhum, é só
# criptografia local.
#
# Depois de rodar:
#   1. Guarde a VAPID_PRIVATE_KEY como variável de ambiente secreta
#      no Render (nunca no código, nunca no front-end).
#   2. A VAPID_PUBLIC_KEY pode ir no front-end sem problema (ela é
#      pública por natureza, serve só pra identificar seu app pro
#      navegador).
#
# Rode: pip install pywebpush (já está no requirements.txt novo)
#       python gerar_chaves_vapid.py
# ==============================================================
import base64
from py_vapid import Vapid02


def gerar():
    v = Vapid02()
    v.generate_keys()

    private_raw = v.private_key.private_numbers().private_value.to_bytes(32, 'big')
    private_b64 = base64.urlsafe_b64encode(private_raw).decode().rstrip('=')

    public_key = v.private_key.public_key()
    numbers = public_key.public_numbers()
    x = numbers.x.to_bytes(32, 'big')
    y = numbers.y.to_bytes(32, 'big')
    public_raw = b'\x04' + x + y
    public_b64 = base64.urlsafe_b64encode(public_raw).decode().rstrip('=')

    print("\n✅ Chaves geradas! Guarde as duas:\n")
    print(f"VAPID_PRIVATE_KEY={private_b64}")
    print(f"VAPID_PUBLIC_KEY={public_b64}")
    print("\n📌 Próximo passo:")
    print("   1. No Render (Environment do serviço da API), adicione:")
    print("      VAPID_PRIVATE_KEY = (a chave privada acima)")
    print("      VAPID_PUBLIC_KEY  = (a chave pública acima)")
    print("      VAPID_EMAIL       = mailto:seu-email@exemplo.com")
    print("   2. No front-end (script.js), cole a VAPID_PUBLIC_KEY na")
    print("      constante VAPID_PUBLIC_KEY do trecho que vou te passar.")


if __name__ == "__main__":
    gerar()
