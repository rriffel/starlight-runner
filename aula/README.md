# Aula: síntese de populações estelares com o STARLIGHT

Esta pasta tem tudo o que é preciso para ajustar os espectros de exemplo com o
STARLIGHT pela interface gráfica (STARLIGHT Runner).

| Arquivo / pasta | O que é |
|---|---|
| `StarlightChains_v04RR_25klines_1000Base.exe` | o STARLIGHT (Linux, 64 bits) |
| `StCv04.C99.config` | parâmetros técnicos do ajuste; janela de normalização 4010–4060 Å, `l_norm` = 4035 Å (média da janela) |
| `Base.BC03.N` | lista da base: 45 SSPs de Bruzual & Charlot (2003), IMF de Chabrier, Z = 0.004, 0.02, 0.05 × 15 idades (1 Myr – 13 Gyr) |
| `BasesDir/` | os espectros das 45 SSPs |
| `spectra/` | os 8 espectros observados (`.csv`: `wavelength,flux_mean`, 3700–6930 Å, sem coluna de erro) |
| `mask/` | uma máscara por espectro (`<espectro>.mask`), com as linhas de emissão ópticas |
| `Masks.EmLines.SDSS.gm` | a mesma máscara de linhas de emissão, para usar como máscara padrão |
| `starlight_gui_config_aula.json` | configuração pronta da interface |
| `run_starlight_aula.py` | a mesma configuração como script Python: roda sem a interface |

## Rodando

1. **Baixe e descompacte a pasta da aula:**
   [aula.tgz](https://github.com/rriffel/starlight-runner/raw/main/aula.tgz)

   ```bash
   tar xzf aula.tgz
   ```

2. **Abra a interface de dentro da pasta `aula`.** O STARLIGHT lê o `.config`
   e a lista da base a partir da pasta onde foi aberto.

   ```bash
   cd aula
   starlight-runner-gui
   ```

3. **Load Config State** → `starlight_gui_config_aula.json`.

4. **Step 3 (STARLIGHT Grid)** → **Run STARLIGHT**. Responda *Yes* para gerar
   os grids. Os CSVs são convertidos sozinhos para `starlight_input/*.spec`, e
   os resultados saem em `out/`.

5. **Step 4 (Results Analysis)**: abra os arquivos de `out/*.out`.

O que a configuração define:

| Campo | Valor |
|---|---|
| Obs Spectra Dir / Pattern | `spectra` / `*.csv` |
| Masks Directory / Extension | `mask` / `.mask` |
| Configuration File | `StCv04.C99.config` |
| Bases Directory / Base File | `BasesDir` / `Base.BC03.N` |
| Output Directory | `out` |
| Fit λ (Å) | 3700–6900 |
| Norm Window (= janela de S/N) / Norm λ for Bases (Å) | 4010–4060 / 4035 |
| Error / Flag spectrum | desligados (os CSVs não têm erro) |

## Rodando sem a interface (script)

`run_starlight_aula.py` faz o mesmo que o Step 3: converte os CSVs, gera os
grids, roda o STARLIGHT e grava a tabela do PyLight em `out/pylight_props.csv`.

```bash
python run_starlight_aula.py          # de dentro de aula/
python aula/run_starlight_aula.py     # ou de qualquer outra pasta
```

Os parâmetros estão no começo do script, em dicionários (`paths`,
`synthesis`, `monte_carlo`, `pylight`): edite e rode de novo. Para massas e
SFRs na tabela, coloque a distância da galáxia em `galaxy_distance` (Mpc).

Na interface:

- **Export Script (.py)** salva a configuração atual como um script desses;
- **Load Script (.py)** preenche a interface a partir de um script (o código
  do script é executado para ler a configuração, mas o STARLIGHT não roda;
  carregue só scripts em que você confia).

## Para explorar

- **Step 1:** carregue um CSV, aplique correções (A_V, z, rebin, cortes), clique
  em **Run Preprocessing** e salve o `.spec`.
- **Step 2:** carregue o espectro, use **Load Optical Preset** ou marque regiões
  com o mouse e salve a máscara. A pasta de máscaras do Step 3 passa a ser a
  pasta onde você salvou. O preset óptico também coloca a janela de
  normalização em 5650–5750 Å e a faixa do ajuste em início + 50 Å até
  fim − 50 Å do espectro salvo.
- **Step 3:** marque **Use standard mask** e escolha `Masks.EmLines.SDSS.gm`
  para usar a mesma máscara em todos os espectros.
- Se a janela de normalização do Step 3 for diferente da do `.config`, ao gerar
  os grids a interface pergunta se deve atualizar o `.config` (o original é
  guardado como `.bak`).
