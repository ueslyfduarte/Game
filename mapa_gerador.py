def criar_mapa_base(largura=800, altura=800):
    img = Image.new('RGB', (largura, altura), color='#2e5c2e')  # floresta de fundo
    draw = ImageDraw.Draw(img)

    # Limites verticais
    sul_y = int(altura * 0.4)
    centro_y = int(altura * 0.85)

    # --- Sul: fazendas e floresta ---
    draw.rectangle([(0, sul_y), (largura, altura)], fill='#b5a642')  # terra clara
    for _ in range(100):
        x = random.randint(0, largura)
        y = random.randint(sul_y, altura)
        cor = random.choice(['#6b8e23', '#556b2f', '#8b7355'])
        draw.ellipse([(x-2, y-2), (x+2, y+2)], fill=cor)

    # --- Centro: cidade ---
    draw.rectangle([(0, centro_y), (largura, sul_y)], fill='#3a3a3a')
    for y in range(centro_y, sul_y, 40):
        draw.line([(0, y), (largura, y)], fill='#555555', width=2)
    for x in range(0, largura, 50):
        draw.line([(x, centro_y), (x, sul_y)], fill='#555555', width=2)
    for _ in range(200):
        x = random.randint(10, largura-40)
        y = random.randint(centro_y+10, sul_y-40)
        w = random.randint(15, 30)
        h = random.randint(15, 30)
        draw.rectangle([(x, y), (x+w, y+h)], fill='#4a4a4a', outline='#222222')

    # --- Norte: zona de quarentena (escura, ruínas) ---
    draw.rectangle([(0, 0), (largura, centro_y)], fill='#1a1a1a')
    for _ in range(60):
        x = random.randint(10, largura-30)
        y = random.randint(10, centro_y-30)
        w = random.randint(10, 20)
        h = random.randint(10, 20)
        draw.rectangle([(x, y), (x+w, y+h)], fill='#2a2a2a', outline='#111111')

    return img
