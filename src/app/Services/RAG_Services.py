from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
import requests
import time
import json
from src.app.HELPERS.Chaves import groq_api_key, manus_api_key, PDF_PATH, URL_MANUS_LIST, URL_MANU_CREATE

def carregar_dados():
  pdf_path = PDF_PATH#"base_conhecimento_producao_industrial.pdf"
  loader = PyPDFLoader(pdf_path)
  documentos = loader.load()
  print("Quantidade de páginas:", len(documentos))
  return documentos

def carregar_chunks(documentos):
  splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=120
  )

  chunks = splitter.split_documents(documentos)
  print("Quantidade de chunks:", len(chunks))
  return chunks

def carregar_embeddings():
  embeddings = HuggingFaceEmbeddings(
      model_name="sentence-transformers/all-MiniLM-L6-v2"
  )

  print("Embeddings criados.")
  return embeddings

def carregar_vectorstore(chunks, embeddings):
  vectorstore = FAISS.from_documents(
    chunks,
    embeddings
  )

  print("Banco vetorial FAISS criado.")
  return vectorstore

def carregar_retriever(vectorstore):
  retriever = vectorstore.as_retriever(
    search_kwargs={
        "k": 4
    }
  )

  print("Retriever criado.")
  return retriever

def carregar_llm():
  llm = ChatGroq(
    #model="llama-3.3-70b-versatile",
    model="openai/gpt-oss-120b",
    api_key=groq_api_key,
    temperature=0
  )
  return llm


def carregar_prompt(dados_producao, retriever):
  # dados_producao = {
  #     "pecas_boas": 15,
  #     "refugos": 8,
  #     "total_produzido": 23
  # }

  consulta = f"""
  Analise esta situação de produção industrial:

  Peças boas: {dados_producao.pecas_boas}
  Refugos: {dados_producao.refugos}
  Total produzido: {dados_producao.total_produzido}

  Procure na base de conhecimento:
  - limites aceitáveis de refugo;
  - critérios de qualidade;
  - procedimentos operacionais;
  - causas possíveis;
  - ações recomendadas.
  """

  documentos_relevantes = retriever.invoke(consulta)

  contexto = "\n\n".join(
      doc.page_content
      for doc in documentos_relevantes
  )

  # print(contexto)
  return contexto

def carregar_consulta(dados_producao, retriever):

  contexto = carregar_prompt(dados_producao, retriever)

  dados_dict = dados_producao.model_dump()

  prompt = f"""
  Você é um analista de produção industrial.

  Analise os dados abaixo utilizando o conhecimento fornecido
  pela empresa.

  DADOS DA PRODUÇÃO:

  {json.dumps(
      dados_dict,
      indent=2,
      ensure_ascii=False
  )}

  CONHECIMENTO RECUPERADO DA EMPRESA:

  {contexto}

  TAREFA:

  1. Calcule a taxa de rendimento.
  2. Calcule a taxa de refugo.
  3. Classifique a situação como:
    NORMAL, ATENÇÃO, ALTA ou CRÍTICA.
  4. Apresente um diagnóstico.
  5. Apresente uma recomendação.

  IMPORTANTE:

  Utilize o conhecimento recuperado como referência
  para suas recomendações.

  Não invente procedimentos ou limites que não estejam
  presentes no conhecimento fornecido.

  Responda de forma objetiva.
  """
  llm = carregar_llm()
  resposta = llm.invoke(prompt)
  # print(f"\n{resposta.content}")
  return resposta.content

def aguardar_resultado(task_id, api_key, intervalo=3):

    url = URL_MANUS_LIST

    while True:

        response = requests.get(
            url,
            headers={
                "x-manus-api-key": api_key
            },
            params={
                "task_id": task_id,
                "order": "desc",
                "limit": 20
            }
        )

        if response.status_code != 200:
            raise Exception(
                f"Erro {response.status_code}: {response.text}"
            )

        dados = response.json()

        # Procura a mensagem do agente
        for mensagem in dados.get("messages", []):

            if "assistant_message" in mensagem:

                resposta = mensagem["assistant_message"]["content"]

                # Verifica se o agente terminou
                status = next(
                    (
                        m["status_update"]["agent_status"]
                        for m in dados.get("messages", [])
                        if "status_update" in m
                    ),
                    None
                )

                if status == "stopped":
                    return resposta

        print("Manus ainda está processando...")
        time.sleep(intervalo)

def analisar_manus(dados_producao, retriever):

  contexto = carregar_prompt(dados_producao, retriever)

  dados_dict = dados_producao.model_dump()

  print("Acionando Manus")

  prompt = f"""
  Você é um analista de produção industrial.

  Analise os dados abaixo utilizando o conhecimento fornecido
  pela empresa.

  DADOS DA PRODUÇÃO:

  {json.dumps(
      dados_dict,
      indent=2,
      ensure_ascii=False
  )}

  CONHECIMENTO RECUPERADO DA EMPRESA:

  {contexto}

  TAREFA:

  1. Calcule a taxa de rendimento.
  2. Calcule a taxa de refugo.
  3. Classifique a situação como:
    NORMAL, ATENÇÃO, ALTA ou CRÍTICA.
  4. Apresente um diagnóstico.
  5. Apresente uma recomendação.

  IMPORTANTE:

  Utilize o conhecimento recuperado como referência
  para suas recomendações.

  Não invente procedimentos ou limites que não estejam
  presentes no conhecimento fornecido.

  Responda de forma objetiva.
  """

  url = URL_MANU_CREATE

  headers = {
      "Content-Type": "application/json",
      "x-manus-api-key": manus_api_key
  }

  payload = {
      "message": {
          "content": [
              {
                  "type": "text",
                  "text": prompt
              }
          ]
      },
      "title": "Análise de Produção com RAG",
      "hide_in_task_list": False,
      "share_visibility": "private",
      "agent_profile": "manus-1.6-lite"
  }

  response = requests.post(
      url,
      headers=headers,
      json=payload
  )

  print(response.status_code)
  print(response.json())

  task_id = response.json()["task_id"]
  print("Task_id: ", task_id)

  time.sleep(2)

  resultado = aguardar_resultado(
    task_id,
    manus_api_key
  )

  # print("RESULTADO:")
  # print(resultado)


  return resultado