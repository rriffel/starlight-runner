import os
from glob import glob
import numpy as np
from scipy.interpolate import interp1d
# --- FORÇAR BACKEND NÃO-INTERATIVO ---
# Isso evita conflitos com o backend Qt do IPython/Mamba ao rodar em loops
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# --- IMPORTAÇÃO DO SEU PACOTE DE REDDENING ---
from ReddeningCorrections import deredden


def cuttel(spec,spec_region=np.array([[0.,13400.],[ 14200.,18000.],[18700.,25000.]])):
        '''
        Function to cut teluric regions. 
        spec = array with Lamb and Flamb and/or eflux
        spec_region= wavelength ranges with useful data. 
        Usage: cuttel(infile,spec_region=array([[0.,13400.],[ 14200.,18000.],[18700.,25000.]])). '''
        if np.shape(spec)[1] == 2:
            lamb=flux=np.array([])
            for mk in spec_region:
                    cut = spec[ (spec[:,0] >= mk[0]) & (spec[:,0] <= mk[1])]
                    lamb=np.append(lamb,cut[:,0])
                    flux=np.append(flux,cut[:,1])
            ret=np.column_stack((lamb,flux))        
            return ret

        if np.shape(spec)[1] == 3:
            lamb=flux=eflux=np.array([])
            for mk in spec_region:
                    cut = spec[ (spec[:,0] >= mk[0]) & (spec[:,0] <= mk[1])]
                    lamb=np.append(lamb,cut[:,0])
                    flux=np.append(flux,cut[:,1])
                    eflux=np.append(eflux,cut[:,2])
            ret=np.column_stack((lamb,flux,eflux))
            return ret





# --- CONFIGURAÇÃO DOS PARÂMETROS FÍSICOS ---
Av = 0.2999
Rv = 3.1
ebv_calculado = Av / Rv  # EBV usado na função deredden

z = 0.013429             # Redshift fornecido

# 1. Encontra todos os arquivos .txt no diretório atual
arquivos_txt = glob("*.txt")

print(f"Encontrados {len(arquivos_txt)} arquivos para processar.\n")

for arquivo_entrada in arquivos_txt:
    print(f"Processando: {arquivo_entrada}...")
    
    try:
        # 2. Carrega os dados originais do arquivo atual
        l, f, ef = np.loadtxt(arquivo_entrada, unpack=True)
        
        # 3. Cria a máscara para remover os NaNs do fluxo e erro
        mascara = ~np.isnan(f) & ~np.isnan(ef)
        l_filtrado = l[mascara]
        f_filtrado = f[mascara]
        ef_filtrado = ef[mascara]
        
        if len(l_filtrado) < 2:
            print(f"-> Erro: Pontos válidos insuficientes em {arquivo_entrada}. Pulando...")
            continue
            
        # 4. PASSO 1: Correção por avermelhamento no espectro original
        espectro_original = np.column_stack((l_filtrado, f_filtrado, ef_filtrado))
        lmb_deredd, f_deredd, ef_deredd = deredden(espectro_original, 'ccm', ebv_calculado)
        
        # 5. PASSO 2: Correção por redshift
        # Move os comprimentos de onda para o referencial de repouso (rest-frame)
        lmb_rest = lmb_deredd / (1.0 + z)
        
        # 6. PASSO 3: Rebinar de 1 em 1 A no referencial de repouso
        lmb_rebin = np.arange(int(lmb_rest[0]), int(lmb_rest[-1]), 1)
        
        interp_f = interp1d(lmb_rest, f_deredd, kind='linear', fill_value="extrapolate")
        interp_ef = interp1d(lmb_rest, ef_deredd, kind='linear', fill_value="extrapolate")
        
        f_rebin = interp_f(lmb_rebin)
        ef_rebin = interp_ef(lmb_rebin)
        
        # 7. Organiza os dados finais em colunas
        dados_finais = np.column_stack((lmb_rebin, f_rebin, ef_rebin))
        
        # Aplica o corte de regiões telúricas
        dados_finais = cuttel(dados_finais, spec_region=np.array([[8650,13000.],[ 14500.,17500.],[19000.,24700.]]))
        
        # Atualiza as variáveis rebinadas para que o plot reflita o corte
        lmb_rebin = dados_finais[:, 0]
        f_rebin = dados_finais[:, 1]
        ef_rebin = dados_finais[:, 2]
        
        # 8. Modifica o nome de saída conforme a especificação desejada
        nome_base, _ = os.path.splitext(arquivo_entrada)
        arquivo_saida = nome_base + "_rebin_deredd.spec"
        arquivo_grafico = nome_base + "_rebin_deredd.png"
        
        # 9. Salva o arquivo final de dados (.spec)
        np.savetxt(
            arquivo_saida, 
            dados_finais, 
            fmt=['%.4f', '%.7e', '%.7e'], 
            delimiter='\t'
        )
        
        # 10. GERAÇÃO DO GRÁFICO (PLOT) COMPLETO
        plt.figure(figsize=(10, 5))
        
        # Plota a linha contínua do fluxo totalmente corrigido
        plt.plot(lmb_rebin, f_rebin, '-', color='black', lw=1.5, label='Fluxo (Dereddened, Z Corr & Rebinned)')
        
        # Define os limites do erro para a região sombreada
        limite_inferior = f_rebin - ef_rebin
        limite_superior = f_rebin + ef_rebin
        
        plt.fill_between(
            lmb_rebin, 
            limite_inferior, 
            limite_superior, 
            color='gray', 
            alpha=0.4,           
            hatch='//',          
            edgecolor='dimgray', 
            label='Região de Erro (ef)'
        )
        
        # Configurações de eixos usando texto puro no título para evitar bugs no Qt
        plt.xlabel(r'Comprimento de Onda em Repouso ($\lambda_{\mathrm{rest}}$) [$\AA$]')
        plt.ylabel('Fluxo Corrigido')
        plt.title(f'Espectro Corrigido: {nome_base} (1. Deredden -> 2. Z Corr -> 3. Rebin)')
        
        plt.legend(loc='upper right')
        plt.grid(True, linestyle='--', alpha=0.5)
        
        plt.tight_layout()
        
        # Salva o gráfico como imagem PNG e fecha a figura
        plt.savefig(arquivo_grafico, dpi=150)
        plt.close()  
        
        print(f"-> Salvo com sucesso: {arquivo_saida} e {arquivo_grafico}\n")
        
    except Exception as e:
        print(f"-> Ocorreu um erro ao processar o arquivo {arquivo_entrada}: {e}\n")

print("Processamento concluído com sucesso!")
