import streamlit as st
from azure.storage.blob import BlobServiceClient
import os
import pymssql
import uuid
import json
from dotenv import load_dotenv

load_dotenv()
blobConnectionString = os.getenv("BLOB_CONNECTION_STRING")
blobContainerName = os.getenv("BLOB_CONTAINER_NAME")
blobAccountName = os.getenv("BLOB_ACCOUNT_NAME")
sqlServer = os.getenv("SQL_SERVER")
sqlDatabase = os.getenv("SQL_DATABASE")
sqlUsername = os.getenv("SQL_USER")
sqlPassword = os.getenv("SQL_PASSWORD")

st.title("Cadastro de Produtos")

# formulário de cadastro de produtos
product_name = st.text_input("Nome do Produto")
product_price = st.number_input("Preço do Produto", min_value=0.0, format="%.2f")
product_description = st.text_area("Descrição do Produto")
product_image = st.file_uploader("Imagem do Produto", type=["jpg", "jpeg", "png"])


# Save image on blob storage
def upload_blob(file):
    blob_service_client = BlobServiceClient.from_connection_string(blobConnectionString)
    container_client = blob_service_client.get_container_client(blobContainerName)
    blob_name = str(uuid.uuid4()) + file.name
    blob_client = container_client.get_blob_client(blob_name)
    blob_client.upload_blob(file.read(), overwrite=True)
    image_url = f"https://{blobAccountName}.blob.core.windows.net/{blobContainerName}/{blob_name}"
    return image_url


def insert_product(name, price, description, product_image):
    try:
        image_url = upload_blob(product_image)
        conn = pymssql.connect(
            server=sqlServer,
            database=sqlDatabase,
            user=sqlUsername,
            password=sqlPassword,
        )
        cursor = conn.cursor()
        cursor.execute(
            f"INSERT INTO Produtos (nome, descricao, preco, imagem_url) VALUES ('{name}', '{description}', {price}, '{image_url}')"
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao inserir produto: {e}")
        return False


def list_products():
    try:
        conn = pymssql.connect(
            server=sqlServer,
            database=sqlDatabase,
            user=sqlUsername,
            password=sqlPassword,
        )
        cursor = conn.cursor(as_dict=True)
        cursor.execute("SELECT * FROM Produtos")
        products = cursor.fetchall()
        conn.close()
        return products
    except Exception as e:
        st.error(f"Erro ao listar produtos: {e}")
        return []


def list_products_screen():
    products = list_products()
    print(products)
    if products:
        # Define o número de cards por linha
        cards_por_linha = 3
        # Cria as colunas iniciais
        cols = st.columns(cards_por_linha)
        for i, product in enumerate(products):
            with cols[i % cards_por_linha]:
                st.markdown(f"### {product['nome']}")
                st.write(f"**Descrição:** {product['descricao']}")
                st.write(f"**Preço:** R$ {product['preco']:.2f}")
                if product["imagem_url"]:
                    html_img = f'<img src="{product["imagem_url"]}" alt="Imagem do Produto" style="width: 200px; height: 200px;">'
                    st.markdown(html_img, unsafe_allow_html=True)
                st.markdown("---")
            # A cada 'cars_por_linha' produtos, se ainda houver produtos, cria novas colunas
            if (i + 1) % cards_por_linha == 0 and (i + 1) < len(products):
                cols = st.columns(cards_por_linha)
    else:
        st.info("Nenhum produto cadastrado.")


if st.button("Salvar Produto"):
    insert_product(product_name, product_price, product_description, product_image)
    st.success("Produto cadastrado com sucesso!")
    list_products_screen()

st.header("Produtos Cadastrados")

if st.button("Listar Produtos"):
    # List products from SQL Server
    list_products_screen()
