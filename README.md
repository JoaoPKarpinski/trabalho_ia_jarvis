# Documentação Geral

## Como rodar o sistema:
#### O sistema está containerizado com docker nas melhores práticas de desenvolvimento, com apenas 1 container para a aplicação, apenas 1 servidor back-end. 
#### As configurações da imagem e do container estão no diretório do projeto backend. O front-end está estático. 
#### O comando ```docker compose up --build``` fará a construção e inicialização do container do servidor e irá expô-lo na porta 8000 da máquina.

## Documentos gerais sobre o trabalho
#### Os documentos de relatórios sobre as informações obrigatórias do sistema, de testes e erros, estão na raíz do projeto, em formato PDF.

## Arquitetura
#### Os documentos relativos à arquitetura do sistema estão anexados ao diretório raiz do repositório, sendo eles o Diagrama de Containers (c4model) e o Diagrama de Componentes (c4model) adaptado ao paradigma funcional.

## Dados teste
#### Os documentos e demais inputs para teste do sistema estão no diretório "documentos_input". Eles já estão inseridos no sistema, no banco chroma e sqlite no dir "backend/data", então não há necessidade de re-processamento. Entretanto, se por acaso houver, os documentos podem ser reutilizados.

## Referências dos documentos utilizados para alimentar o sistema:
- Documento engenharia-de-requisitos.pdf: https://www.maxwell.vrac.puc-rio.br/6954/6954_3.PDF
- Documento arquitetura-serverlesspdf.pdf: https://monografias.dcc.ufmg.br/wp-content/uploads/LucasPereiraCarvalho.pdf
- Documento site-reliability-engineering.pdf: https://www.opservices.com.br/files/ebook-site-reliability-engineering.pdf
- Documento padroes-em-microsservicos.pdf: https://repositorio.ifg.edu.br/bitstream/prefix/700/1/TCC_Padroes%20para%20produ%C3%A7%C3%A3o%20de%20aplica%C3%A7%C3%B5es%20utilizando%20Microsservi%C3%A7os.pdf
- Documento aplicacao-arquitetura-hexagonal.pdf: https://bdta.abcd.usp.br/directbitstream/e52e41a9-38c2-47f3-a1f8-c0e8dbc123ea/B%C3%81RBARA_MINITTI.pdf
- Documento padroes-de-resiliencia.pdf: https://www.researchgate.net/publication/396864276_Padroes_de_Resiliencia_em_Arquiteturas_de_Microsservicos_Uma_Analise_em_Ambientes_de_Alta_Demanda
- Documento arquitetura-orientada-a-eventos.pdf: https://thedevconf.s3.sa-east-1.amazonaws.com/presentations/TDC2021TRF/cloud/ICD-8228_2021-08-27T111600_Criando+solu%C3%A7%C3%B5es+orientadas+a+eventos+de+alto+n%C3%ADvel+com+serverless.pdf
- Documento domain-driven-development.pdf: https://www.ricardopedias.com.br/assets/docs/ddd-referencia.pdf
- Documento divida-tecnica.pdf: https://sol.sbc.org.br/index.php/sbqs/article/download/15290/15133
- Documento testes-de-software.pdf: https://web.icmc.usp.br/SCATUSU/RT/Notas_Didaticas/nd_65.pdf

## Ferramentas utilizadas:
#### Stack: 
- Fast-API para servidor
- Vue.JS para desenvolver o front-end
- SQLite como SGBD
- ChromaDB como banco vetorial
- Github Copilot para desenvolvimento geral
- Docker para conteinerização

## Chunking:
A abordagem atual de chunking consiste na escolha, atualmente arbitrária, do tamanho do chunk em 1000 caracteres, 
com valor de overlapping de 200 caracteres. A abordagem não é a atual e não é definitiva. Os planos são de 
implementar um particionamento semântico na próxima iteração de desenvolvimento focada nas melhorias.