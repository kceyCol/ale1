import fitz  # Importa a biblioteca PyMuPDF
import os

def extrair_texto_de_pdf(caminho_pdf, caminho_txt):
    """
    Extrai o texto de um arquivo PDF e o salva em um arquivo .txt.

    :param caminho_pdf: O caminho para o arquivo PDF de entrada.
    :param caminho_txt: O caminho para o arquivo .txt de saída.
    """
    try:
        # Abre o arquivo PDF
        documento = fitz.open(caminho_pdf)
        
        texto_completo = ""
        
        # Itera por cada página do documento
        for pagina_num in range(len(documento)):
            pagina = documento.load_page(pagina_num)  # Carrega a página
            texto_completo += pagina.get_text()  # Extrai o texto da página
            texto_completo += "\n--- Fim da Página {} ---\n\n".format(pagina_num + 1) # Adiciona um separador opcional

        # Salva o texto extraído no arquivo .txt
        with open(caminho_txt, "w", encoding="utf-8") as arquivo_saida:
            arquivo_saida.write(texto_completo)
            
        print(f"Sucesso! Texto extraído de '{caminho_pdf}' e salvo em '{caminho_txt}'")

    except Exception as e:
        print(f"Ocorreu um erro: {e}")

def listar_pdfs_na_pasta():
    """
    Lista todos os arquivos PDF na pasta atual.
    """
    pdfs = [arquivo for arquivo in os.listdir('.') if arquivo.lower().endswith('.pdf')]
    return pdfs

def selecionar_pdf():
    """
    Permite ao usuário selecionar um arquivo PDF da pasta atual.
    """
    pdfs = listar_pdfs_na_pasta()
    
    if not pdfs:
        print("Nenhum arquivo PDF encontrado na pasta atual.")
        nome_arquivo = input("Digite o nome completo do arquivo PDF (com extensão): ")
        return nome_arquivo
    
    print("\nArquivos PDF encontrados na pasta atual:")
    for i, pdf in enumerate(pdfs, 1):
        print(f"{i}. {pdf}")
    
    print(f"{len(pdfs) + 1}. Digitar nome de arquivo manualmente")
    
    while True:
        try:
            escolha = int(input(f"\nEscolha um arquivo (1-{len(pdfs) + 1}): "))
            
            if 1 <= escolha <= len(pdfs):
                return pdfs[escolha - 1]
            elif escolha == len(pdfs) + 1:
                nome_arquivo = input("Digite o nome completo do arquivo PDF (com extensão): ")
                return nome_arquivo
            else:
                print("Opção inválida. Tente novamente.")
        except ValueError:
            print("Por favor, digite um número válido.")

# --- EXECUÇÃO PRINCIPAL ---
if __name__ == "__main__":
    print("=== Extrator de Texto de PDF ===")
    
    # Seleciona o arquivo PDF
    nome_arquivo_pdf = selecionar_pdf()
    
    # Verifica se o arquivo existe
    if not os.path.exists(nome_arquivo_pdf):
        print(f"Erro: O arquivo '{nome_arquivo_pdf}' não foi encontrado.")
        exit(1)
    
    # Gera o nome do arquivo de saída baseado no PDF selecionado
    nome_base = os.path.splitext(nome_arquivo_pdf)[0]
    nome_arquivo_txt = f"{nome_base}_texto_extraido.txt"
    
    print(f"\nProcessando: {nome_arquivo_pdf}")
    print(f"Arquivo de saída: {nome_arquivo_txt}")
    
    # Chama a função para executar a extração
    extrair_texto_de_pdf(nome_arquivo_pdf, nome_arquivo_txt)