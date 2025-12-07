# 🫀 CardioBot - Assistente Inteligente de Cuidados Pré e Pós-Operatórios
## Autora: Gabriela Toledo 
Trabalho Final da disciplina de **Tópicos Especiais em Programação III (2025/2)** do curso de **Informática Biomédica (UFCSPA)**.


## 1. Visão Geral do Projeto

O **CardioBot** é uma aplicação web Full Stack desenvolvida para auxiliar pacientes em recuperação de cirurgia cardíaca. O sistema resolve o problema da falta de informação acessível e personalizada no período pós-operatório, oferecendo:

1.  **IA Local com RAG (Backend):** Respostas seguras baseadas em estudos acadêmicos (PDFs), garantindo privacidade total dos dados.
2.  **Monitoramento Diário (CRUD Multi-usuário):** Um diário digital para registro de sintomas e evolução clínica, com histórico individualizado por paciente.
3.  **Orientação Climática (API Externa):** Monitoramento em tempo real da temperatura local para prevenção de riscos cardiovasculares associados ao frio/calor extremos.
4.  **Sistema de Login:** Controle de acesso para garantir que cada paciente veja apenas os seus próprios dados.

---

## 2. Arquitetura Técnica

O projeto segue uma arquitetura **MVC (Model-View-Controller)** adaptada para microsserviços locais:

* **Frontend (View):** HTML5, JavaScript (ES6) e Tailwind CSS. Interface responsiva com foco em acessibilidade.
* **Backend (Controller):** Python com Framework Flask, gerenciando as rotas da API RESTful, autenticação e orquestração dos serviços.
* **Banco de Dados (Model):**
    * **Relacional:** SQLite (para Usuários e Diário do Paciente).
    * **Vetorial:** ChromaDB (Indexação semântica da base de conhecimento RAG).
* **LLM:** Llama 3 (8B Parameters) rodando localmente via `llama-cpp-python`.

---

## 3. Banco de Dados

O sistema utiliza **SQLite**. Com a implementação do login, o banco foi estruturado em duas tabelas relacionadas:

### Tabela: `usuarios`
Armazena as credenciais de acesso.
| Campo   | Tipo   | Descrição                          |
| `email` | `TEXT` | Chave Primária (PK). Identificador único. |
| `senha` | `TEXT` | Senha de acesso.                   |
| `nome`  | `TEXT` | Nome de exibição do paciente.      |

### Tabela: `diario`
Armazena as anotações clínicas vinculadas a um usuário.
| Campo      | Tipo       | Descrição                                      |
| `id`       | `INTEGER`  | Chave Primária (PK), Auto-incremento.          |
| `texto`    | `TEXT`     | Conteúdo da anotação/sintoma.                  |
| `paciente` | `TEXT`     | Chave Estrangeira (Vincula ao `email` do usuário). |
| `data`     | `DATETIME` | Carimbo de tempo automático.                   |

---

## 4. Usuários de Teste 

2 perfis pré configurados para validar senha e isolamento das notas do CRUD

| Perfil         | E-mail (Login)     | Senha  | Cenário de Teste |
| **Paciente 1** | `joao@cardio.com`  | `1234` | Pós-operatório recente. |
| **Paciente 2** | `maria@cardio.com` | `1234` | Pré-operatório. |

---

## 5. Como Executar

### Pré-requisitos
> É necessário ter **Python 3.9** ou superior instalado.
> Conexão com internet ativa (para carregamento do Tailwind CSS e consulta à API de Clima).

### 5.1. Instalação das Dependências
Abra o terminal na pasta do projeto e execute:
```bash
pip install -r requirements.txt
# Para usuários de Mac/Linux, utilize: pip3 install -r requirements.txt