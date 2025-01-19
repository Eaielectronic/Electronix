from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
import os
import re
from bs4 import BeautifulSoup

app = Flask(__name__)

# Chemins pour les fichiers sauvegardés
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static/uploads")
IMAGES_FOLDER = os.path.join(UPLOAD_FOLDER, "images")
ARTICLES_FOLDER = os.path.join(UPLOAD_FOLDER, "articles")

# Configurer le dossier d'upload
os.makedirs(IMAGES_FOLDER, exist_ok=True)
os.makedirs(ARTICLES_FOLDER, exist_ok=True)

@app.route("/")
def index():
    """Liste tous les articles disponibles."""
    articles = os.listdir(ARTICLES_FOLDER)
    # Associe chaque article à son URL
    articles_with_urls = [
        (article, url_for("view_article", article_name=article))
        for article in articles
    ]
    return render_template("index.html", articles=articles_with_urls)

@app.route("/create", methods=["GET", "POST"])
def create_article():
    """Page pour créer un article."""
    if request.method == "POST":
        title = request.form.get("title")  # Titre de l'article
        content = request.form.get("content")  # Contenu de l'article

        # Log les données pour vérifier la soumission
        print(f"Titre: {title}, Contenu: {content}")  # Affiche les données dans la console

        # Vérifie que le titre et le contenu existent
        if title and content:
            safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
            article_folder = os.path.join(ARTICLES_FOLDER, safe_title)
            os.makedirs(article_folder, exist_ok=True)

            updated_content = adjust_image_paths(content, article_folder)
            filepath = os.path.join(article_folder, "index.html")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(render_template(
                    "main_template.html",
                    page_title=title,
                    article_content=updated_content
                ))

            return redirect(url_for("index"))

    return render_template("create.html")

@app.route('/edit/<article_name>', methods=['GET', 'POST'])
def edit_article(article_name):
    """Modifier un article."""
    article_folder = os.path.join('static', 'uploads', 'articles', article_name)
    article_path = os.path.join(article_folder, 'index.html')

    if not os.path.isfile(article_path):
        return f"Erreur: l'article {article_name} n'existe pas ou n'est pas un fichier HTML.", 404

    if request.method == 'POST':
        # Sauvegarder uniquement le contenu dans <div class="content-container">
        content = request.form['content']
        
        # Lire le fichier HTML existant
        with open(article_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        # Trouver la div avec la classe 'content-container' et mettre à jour son contenu
        content_div = soup.find('div', class_='content-container')
        if content_div:
            content_div.clear()  # Supprimer le contenu actuel
            content_div.append(content)  # Ajouter le nouveau contenu

        # Sauvegarder les changements dans le fichier HTML
        with open(article_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))

        return redirect(url_for('index'))  # Rediriger vers la page d'accueil ou la liste des articles

    # Charger l'article et extraire le contenu de la div "content-container"
    article_content = ''
    with open(article_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
        content_div = soup.find('div', class_='content-container')
        if content_div:
            article_content = content_div.get_text()  # Extraire uniquement le texte de la div

    return render_template('create.html', article_title=article_name, article_content=article_content)

@app.route("/uploads/images/<filename>")
def uploaded_image(filename):
    """Servir les images uploadées."""
    return send_from_directory(IMAGES_FOLDER, filename)

@app.route("/article/<article_name>")
def view_article(article_name):
    """Affiche un article sauvegardé."""
    article_folder = os.path.join(ARTICLES_FOLDER, article_name)
    filepath = os.path.join(article_folder, "index.html")

    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return content  # Renvoie directement le contenu HTML
    return "Article not found", 404

@app.route("/upload_image", methods=["POST"])
def upload_image():
    """Uploader une image pour l'insérer dans un article."""
    if "file" in request.files:
        image = request.files["file"]
        if image.filename != "":
            filepath = os.path.join(IMAGES_FOLDER, image.filename)
            image.save(filepath)

            # Retourner un chemin relatif correct pour TinyMCE
            image_url = f"static/uploads/images/{image.filename}"
            return jsonify({"location": image_url})
    return jsonify({"error": "Invalid upload"}), 400

def adjust_image_paths(content, article_folder):
    """
    Corrige les chemins des images dans le contenu HTML pour qu'ils pointent vers le dossier spécifique.
    Copie également les images dans le dossier de l'article.
    """
    def replace_image_path(match):
        image_filename = match.group(1)
        source_path = os.path.join(IMAGES_FOLDER, image_filename)
        dest_path = os.path.join(article_folder, "images", image_filename)

        # Crée le dossier "images" dans le dossier de l'article
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        # Copier l'image dans le dossier de l'article
        if os.path.exists(source_path):
            if not os.path.exists(dest_path):  # Évite les copies redondantes
                os.rename(source_path, dest_path)

        # Retourne le chemin relatif
        return f'src="images/{image_filename}"'

    return re.sub(r'src="static/uploads/images/(.*?)"', replace_image_path, content)

if __name__ == "__main__":
    app.run(debug=True)
