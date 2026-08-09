from PIL import Image, ImageDraw
import random

def criar_mapa_base(largura=800, altura=800):
    img = Image.new('RGB', (largura, altura), color='#2e5c2e')
    draw = ImageDraw.Draw(img)

    # Limites verticais
    sul_y = int(altura * 0.4)       # abaixo disso é sul (fazendas)
    centro_y = int(altura * 0.85)   # entre centro_y e sul_y = cidade

    # --- Sul: fazendas e floresta leve ---
    draw.rectangle([(0, sul_y), (largura, altura)], fill='#b5a642')
    for _ in range(150):
        x = random.randint(0, largura)
        y = random.randint(sul_y, altura)
        cor = random.choice(['#6b8e23', '#556b2f', '#8b7355', '#3a6b3a'])
        draw.ellipse([(x-2, y-2), (x+2, y+2)], fill=cor)
    # Celeiros
    for _ in range(20):
        x = random.randint(0, largura-20)
        y = random.randint(sul_y, altura-20)
        draw.rectangle([(x, y), (x+15, y+10)], fill='#8b0000', outline='#4a0000')

    # --- Centro: cidade densa ---
    draw.rectangle([(0, centro_y), (largura, sul_y)], fill='#3a3a3a')
    for y in range(centro_y, sul_y, 40):
        draw.line([(0, y), (largura, y)], fill='#555555', width=2)
    for x in range(0, largura, 50):
        draw.line([(x, centro_y), (x, sul_y)], fill='#555555', width=2)
    for _ in range(250):
        x = random.randint(10, largura-40)
        y = random.randint(centro_y+10, sul_y-40)
        w = random.randint(15, 30)
        h = random.randint(15, 30)
        draw.rectangle([(x, y), (x+w, y+h)], fill='#4a4a4a', outline='#222222')

    # --- Norte: zona de quarentena (escura, ruínas) ---
    draw.rectangle([(0, 0), (largura, centro_y)], fill='#1a1a1a')
    for _ in range(80):
        x = random.randint(10, largura-30)
        y = random.randint(10, centro_y-30)
        w = random.randint(10, 20)
        h = random.randint(10, 20)
        draw.rectangle([(x, y), (x+w, y+h)], fill='#2a2a2a', outline='#111111')
    # Pontos vermelhos (perigo)
    for _ in range(30):
        x = random.randint(20, largura-20)
        y = random.randint(20, centro_y-20)
        draw.ellipse([(x-1, y-1), (x+1, y+1)], fill='#660000')

    return img
