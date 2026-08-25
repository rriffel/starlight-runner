import re

file_path = "/home/riffel/Dropbox/programas/Develp/starlight-runner/starlight_runner/main_gui.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

replacements = {
    # InteractiveMaskDialog
    "Janela Interativa de Máscara (CreateMasks Mode)": "Interactive Mask Studio (CreateMasks Mode)",
    "<b>Clique Esquerdo:</b>": "<b>Left Click:</b>",
    "Peso 0.0 (Vermelho - Excluir)": "Weight 0.0 (Red - Exclude)",
    "Peso 2.0 (Verde - Destacar)": "Weight 2.0 (Green - Emphasize)",
    "Padrão Óptico (CreateMasks)": "Optical Preset (CreateMasks)",
    "Padrão NIR": "NIR Preset",
    "Carregar .mask": "Load .mask",
    "Salvar .mask": "Save .mask",
    "Limpar Tudo": "Clear All",
    "✓ Concluir Edição (ou tecla 'q')": "✓ Finish Editing (or 'q' key)",
    "<b>Botão Direito (Right-Click)</b>: 1º e 2º clique marca Peso 0.0 (Vermelho)  |  <b>Botão do Meio (Middle-Click)</b>: 1º e 2º clique marca Peso 2.0 (Verde)  |  <b>Tecla 'd'</b>: Apaga a região sob o cursor  |  <b>Tecla 'q' ou 'Esc'</b>: Conclui e fecha a janela": "<b>Right-Click</b>: 1st & 2nd click mark Weight 0.0 (Red)  |  <b>Middle-Click</b>: 1st & 2nd click mark Weight 2.0 (Green)  |  <b>'d' key</b>: Delete region under cursor  |  <b>'q' or 'Esc' key</b>: Finish and close",
    "Regiões Mascaradas": "Masked Regions",
    "\"Peso\"": "\"Weight\"",
    "Remover Selecionada": "Remove Selected",
    "Pronto para mascarar. Clique nos extremos da linha ou use o botao direito.": "Ready to mask. Click on line extremes or use right-click.",
    "Abrir Arquivo de Máscara (.mask)": "Open Mask File (.mask)",
    "Erro ao carregar máscara": "Error loading mask",
    "Máscara carregada de ": "Mask loaded from ",
    " interval(os).": " interval(s).",
    "Salvar Máscara STARLIGHT": "Save STARLIGHT Mask",
    "Máscara salva em ": "Mask saved to ",
    "Máscara Salva": "Mask Saved",
    "Arquivo de máscara salvo com sucesso:\\n": "Mask file successfully saved:\\n",
    "Erro ao salvar máscara": "Error saving mask",
    "Clique no 2o ponto para aplicar mascara com peso ": "Click 2nd point to apply mask with weight ",
    "0.0 (Excluir)": "0.0 (Exclude)",
    "2.0 (Destacar)": "2.0 (Emphasize)",
    "Regiao adicionada: ": "Region added: ",
    "Selecao cancelada.": "Selection canceled.",
    "Mascara removida em ": "Mask removed at ",

    # InteractiveCutDialog
    "Janela Interativa de Corte (Telúricas / Extremidades)": "Interactive Trimming (Telluric / Extremities)",
    "<b>Corte Interativo de Espectro:</b>": "<b>Interactive Spectrum Trimming:</b>",
    "Limpar Cortes": "Clear Cuts",
    "✓ Concluir e Fechar (ou tecla 'q')": "✓ Finish and Close (or 'q' key)",
    "<b>Clique 1 e Clique 2</b>: Seleciona os limites da região a ser cortada  |  <b>Botão Direito</b>: Também inicia/termina corte  |  <b>Tecla 'd'</b>: Remove o corte sob o cursor  |  <b>Tecla 'q' ou 'Esc'</b>: Conclui e fecha a janela": "<b>Click 1 & Click 2</b>: Select limits of region to cut  |  <b>Right-Click</b>: Also starts/ends cut  |  <b>'d' key</b>: Remove cut under cursor  |  <b>'q' or 'Esc' key</b>: Finish and close",
    "Clique no 1º ponto para iniciar o corte.": "Click 1st point to start cutting.",
    "Clique no 2o ponto para cortar.": "Click 2nd point to cut.",
    "Região cortada adicionada: ": "Cut region added: ",
    "Corte removido em ": "Cut removed at ",
    "Regiao Cortada": "Cut Region"
}

for pt, en in replacements.items():
    content = content.replace(pt, en)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Translation applied!")
