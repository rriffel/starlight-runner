import re

file_path = "/home/riffel/Dropbox/programas/Develp/starlight-runner/starlight_runner/main_gui.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

replacements = {
    # Main Window tabs and general UI
    "1. Pré-processamento de Dados": "1. Data Preprocessing",
    "2. Máscara & Regiões": "2. Spectral Masking",
    "3. Geração de Grade (STARLIGHT)": "3. STARLIGHT Grid",
    "4. Resultados & Análise": "4. Results & Analysis",
    "Pronto — Selecione ou carregue um espectro para começar.": "Ready — Select or load a spectrum to begin.",
    
    # Preprocessing tab
    "Carregar Espectro...": "Load Spectrum...",
    "Redshift/Velocidade Radial": "Redshift/Radial Velocity",
    "Cortes Telúricos (Opcional)": "Telluric Cuts (Optional)",
    "Aplicar Deslocamento": "Apply Shift",
    "Restaurar Espectro": "Restore Spectrum",
    "Processar & Re-bin": "Process & Re-bin",
    "Nenhum Espectro Carregado": "No Spectrum Loaded",
    "Selecione um espectro e aplique o processamento.": "Select a spectrum and apply processing.",
    "Corrigir Extinção Galáctica (Opcional)": "Galactic Extinction Correction (Optional)",
    "E(B-V)": "E(B-V)",
    "Lei de Extinção": "Extinction Law",
    "Visualizar Detached": "View Detached",
    "Diálogo Detached": "Detached Dialog",
    "Reamostragem e Corte": "Resampling and Trimming",
    "Passo de Reamostragem (dA)": "Resampling Step (dA)",
    "Cortar Regiões nas Bordas": "Trim Boundary Regions",
    "Visualização e Configuração do Espectro": "Spectrum Visualization and Setup",
    
    # Masking tab
    "Máscara Espectral de Emissão": "Spectral Emission Mask",
    "Configurações Manuais e Rápidas": "Manual & Quick Settings",
    "Salvar .mask": "Save .mask",
    "Painel de Mascaramento Interativo": "Interactive Masking Panel",
    "Abrir Modo Interativo Completo (Detached)": "Open Full Interactive Mode (Detached)",
    
    # Starlight Grid tab
    "Geração de Arquivos de Grade e Execução": "Grid Generation & Execution",
    "Diretórios e Arquivos Básicos (Passo 3)": "Basic Directories & Files",
    "Espectros de Entrada (.spec)": "Input Spectra (.spec)",
    "Bases (BaseDir)": "Bases (BaseDir)",
    "Sintéticos (OutDir)": "Synthetics (OutDir)",
    "Máscara Padrão (Opcional)": "Default Mask (Optional)",
    "Configuração (.config)": "Configuration (.config)",
    "Manifesto de Base (.base)": "Base Manifest (.base)",
    "Executável (Starlight)": "Executable (Starlight)",
    "Parâmetros Físicos e Limites": "Physical Parameters & Limits",
    "Velocidade Inicial (v0)": "Initial Velocity (v0)",
    "Dispersão (vd)": "Velocity Dispersion (vd)",
    "Reddening Fixo (Kin)": "Fixed Reddening (Kin)",
    "Parâmetros de Ajuste e Extinção": "Fitting & Extinction Parameters",
    "Ação e Progresso": "Action & Progress",
    "Gerar Arquivos de Grade": "Generate Grid Files",
    "Iniciar Ajuste (Executar Starlight)": "Start Fitting (Run Starlight)",
    
    # Results tab
    "Nenhum arquivo executado ainda.": "No files executed yet.",
    "Resultados e Síntese Populacional": "Results & Population Synthesis",
    "Ajuste Espectral e Resíduos": "Spectral Fit & Residuals",
    "Vetores Populacionais (Idades / Metalicidade)": "Population Vectors (Ages / Metallicity)",
    "Selecione um Arquivo de Saída:": "Select an Output File:",
    "Carregar Saída": "Load Output",
    
    "Arquivo salvo": "File saved",
    "Espectro carregado:": "Spectrum loaded:",
    "Extensão de Espectro / Padrão": "Spectrum Extension / Pattern"
}

for pt, en in replacements.items():
    content = content.replace(pt, en)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Translation 2 applied!")
