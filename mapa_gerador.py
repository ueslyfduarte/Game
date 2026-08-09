from PIL import Image, ImageDraw
import random

def criar_mapa_base(largura=800, altura=800):
    img = Image.new('RGB', (largura, altura), color='#2e5c2e')
    draw = ImageDraw.Draw(img)

    # Conversão de latitude para coordenada y (0 = topo/norte, 1 = base/sul)
    # Norte (lat 0.85 a 1) -> y de 0 a 0.15*altura
    # Centro (lat 0.4 a 0.85) -> y de 0.15*altura a 0.6*altura
    # Sul (lat 0 a 0.4) -> y de 0.6*altura a altura
    norte_fim = int(altura * 0.15)   # fim do norte, início do centro
    centro_fim = int(altura * 0.6)   # fim do centro, início do sul

    # --- Norte (zona de quarentena, escura) ---
    draw.rectangle([(0, 0), (largura, norte_fim)], fill='#1a1a1a')
    for _ in range(80):
        x = random.randint(10, largura-30)
        y = random.randint(10, norte_fim-30)
        w = random.randint(10, 20)
        h = random.randint(10, 20)
        draw.rectangle([(x, y), (x+w, y+h)], fill='#2a2a2a', outline='#111111')
    for _ in range(30):
        x = random.randint(20, largura-20)
        y = random.randint(20, norte_fim-20)
        draw.ellipse([(x-1, y-1), (x+1, y+1)], fill='#660000')

    # --- Centro (cidade densa) ---
    draw.rectangle([(0, norte_fim), (largura, centro_fim)], fill='#3a3a3a')
    for y in range(norte_fim, centro_fim, 40):
        draw.line([(0, y), (largura, y)], fill='#555555', width=2)
    for x in range(0, largura, 50):
        draw.line([(x, norte_fim), (x, centro_fim)], fill='#555555', width=2)
    for _ in range(250):
        x = random.randint(10, largura-40)
        y = random.randint(norte_fim+10, centro_fim-40)
        w = random.randint(15, 30)
        h = random.randint(15, 30)
        draw.rectangle([(x, y), (x+w, y+h)], fill='#4a4a4a', outline='#222222')

    # --- Sul (fazendas e floresta) ---
    draw.rectangle([(0, centro_fim), (largura, altura)], fill='#b5a642')
    for _ in range(150):
        x = random.randint(0, largura)
        y = random.randint(centro_fim, altura)
        cor = random.choice(['#6b8e23', '#556b2f', '#8b7355', '#3a6b3a'])
        draw.ellipse([(x-2, y-2), (x+2, y+2)], fill=cor)
    for _ in range(20):
        x = random.randint(0, largura-20)
        y = random.randint(centro_fim, altura-20)
        draw.rectangle([(x, y), (x+15, y+10)], fill='#8b0000', outline='#4a0000')

    return img
