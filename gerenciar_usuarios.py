1# gerenciar_usuarios.py
import json
import hashlib
import os
from datetime import datetime

ARQUIVO_USUARIOS = "usuarios.json"

def hash_cpf(cpf):
    """Remove pontuações e criptografa o CPF para segurança."""
    cpf_limpo = cpf.replace(".", "").replace("-", "").strip()
    return hashlib.sha256(cpf_limpo.encode('utf-8')).hexdigest()

def carregar_usuarios():
    if os.path.exists(ARQUIVO_USUARIOS):
        with open(ARQUIVO_USUARIOS, "r", encoding="utf-8") as f:
            return json.load(f).get("usuarios", [])
    return []

def salvar_usuarios(usuarios):
    with open(ARQUIVO_USUARIOS, "w", encoding="utf-8") as f:
        json.dump({"usuarios": usuarios}, f, indent=4, ensure_ascii=False)

def cadastrar_ou_atualizar(email, cpf, nome="", ativo=True):
    usuarios = carregar_usuarios()
    email = email.lower().strip()
    
    for i, user in enumerate(usuarios):
        if user["email"] == email:
            usuarios[i]["cpf_hash"] = hash_cpf(cpf)
            usuarios[i]["nome"] = nome
            usuarios[i]["ativo"] = ativo
            salvar_usuarios(usuarios)
            print(f"✅ Usuário {email} ATUALIZADO!")
            return
            
    usuarios.append({
        "email": email,
        "cpf_hash": hash_cpf(cpf),
        "nome": nome,
        "ativo": ativo,
        "data_cadastro": datetime.now().strftime("%Y-%m-%d")
    })
    salvar_usuarios(usuarios)
    print(f"✅ Usuário {email} CADASTRADO com sucesso!")

def listar_usuarios():
    usuarios = carregar_usuarios()
    print("\n" + "="*60)
    print("📋 USUÁRIOS CADASTRADOS")
    print("="*60)
    for u in usuarios:
        status = "🟢 ATIVO" if u["ativo"] else "🔴 BLOQUEADO"
        print(f"Email: {u['email']} | Nome: {u['nome']} | Status: {status}")
    print("="*60 + "\n")

if __name__ == "__main__":
    print("\n--- GERENCIADOR DE USUÁRIOS GAMMA POINTS ---")
    print("1. Cadastrar/Atualizar Usuário")
    print("2. Listar Usuários")
    print("3. Bloquear Usuário")
    print("4. Sair")
    
    opcao = input("\nEscolha uma opção (1-4): ").strip()
    
    if opcao == "1":
        email = input("E-mail do usuário: ").strip()
        cpf = input("CPF (apenas números ou com pontuação): ").strip()
        nome = input("Nome completo (opcional): ").strip()
        cadastrar_ou_atualizar(email, cpf, nome, ativo=True)
    elif opcao == "2":
        listar_usuarios()
    elif opcao == "3":
        email = input("E-mail do usuário a bloquear: ").strip()
        usuarios = carregar_usuarios()
        for u in usuarios:
            if u["email"] == email.lower():
                u["ativo"] = False
                salvar_usuarios(usuarios)
                print(f"🚫 Usuário {email} BLOQUEADO!")
                break
    input("\nPressione Enter para sair...")