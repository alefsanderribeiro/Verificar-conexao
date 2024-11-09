# Monitor de Ping

Um programa simples e eficiente para monitoramento contínuo de ping com registro de histórico e logs.

## 📋 Características

- Interface de console amigável
- Histórico dos últimos 5 endereços monitorados
- Logs detalhados com data e hora
- Suporte para Windows e Linux
- Monitoramento em tempo real
- Salvamento automático de logs

## 🚀 Instalação

### Pré-requisitos

- Python 3.6 ou superior
- cx_Freeze (para criar o executável)

### Instalando as dependências
```bash
pip install cx_freeze
```

### Criando o executável

```bash
python setup.py build
```

## 💻 Como usar

1. Execute o programa:
   - Via Python: `python main.py`
   - Ou use o executável gerado: `Monitor de Ping.exe`

2. Selecione uma opção:
   - Escolha um endereço do histórico
   - Digite 0 para inserir um novo endereço
   - Pressione Enter para usar o padrão (8.8.8.8)

3. O programa iniciará o monitoramento e mostrará:
   - Status da conexão
   - Tempo de resposta em ms
   - Logs em tempo real

4. Para encerrar, pressione `Ctrl+C`

## 📁 Estrutura de arquivos

```
Monitor de Ping/
│
├── main.py              # Código principal
├── setup.py            # Configuração para criar executável
├── historico_ping.json # Arquivo de histórico
│
└── logs/               # Pasta com arquivos de log
    └── ping_log_YYYYMMDD_HHMMSS.txt
```

## 📊 Formato do Log

Os logs são salvos em arquivos de texto com o seguinte formato:
```
Monitoramento de ping para [endereço]
Início: YYYY-MM-DD HH:MM:SS
--------------------------------------------------
[HH:MM:SS] Status: Sucesso - Ping: XXms
[HH:MM:SS] Status: Timeout
[HH:MM:SS] Status: Falha na conexão
```

## ⚙️ Configurações

O programa inclui algumas configurações padrão:
- Mantém histórico dos últimos 5 endereços
- Atualiza a cada 1 segundo
- Interface em cores (verde sobre preto no Windows)
- Janela do console otimizada (100x30 caracteres)

## 🤝 Contribuindo

Sinta-se à vontade para contribuir com este projeto:

1. Faça um Fork do projeto
2. Crie uma Branch para sua Feature (`git checkout -b feature/AmazingFeature`)
3. Faça o Commit de suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Faça o Push para a Branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## ✨ Autor

Alefe - [GitHub](https://github.com/seu-usuario)

## 🔄 Versão

- Versão atual: 0.0.1

## 📞 Suporte

- Abra uma issue neste repositório
- Entre em contato via [email](alefsander.pvh14@gmail.com)

---
⌨️ com ❤️ por [Alefe](https://github.com/alefsanderribeiro)
```
