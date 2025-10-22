"""
Générateur de bulletins PDF pour SchoolPro
Utilise ReportLab pour créer des bulletins personnalisables avec graphiques
"""

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.platypus.frames import Frame
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics import renderPDF
from io import BytesIO
import os
from django.conf import settings
from django.http import HttpResponse
from datetime import datetime
from .models import Etudiant, Bulletin
from .utils import calculer_moyenne_etudiant, get_appreciation, calculer_rang_etudiant


class BulletinPDFGenerator:
    """Générateur de bulletins PDF personnalisés"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Configure les styles personnalisés"""
        # Style pour le titre
        self.styles.add(ParagraphStyle(
            name='Title',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1,  # Centré
            textColor=colors.darkblue
        ))
        
        # Style pour les sous-titres
        self.styles.add(ParagraphStyle(
            name='Subtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=20,
            textColor=colors.darkblue
        ))
        
        # Style pour les informations personnelles
        self.styles.add(ParagraphStyle(
            name='Info',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=10,
            leftIndent=20
        ))
        
        # Style pour les matières
        self.styles.add(ParagraphStyle(
            name='Matiere',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=5,
            leftIndent=10
        ))
    
    def create_header(self, doc, etudiant, classe, annee_scolaire):
        """Crée l'en-tête du bulletin"""
        story = []
        
        # Logo de l'école (si disponible)
        logo_path = os.path.join(settings.MEDIA_ROOT, 'logo_ecole.png')
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=2*inch, height=1.5*inch)
            logo.hAlign = 'CENTER'
            story.append(logo)
            story.append(Spacer(1, 20))
        
        # Titre du bulletin
        title = Paragraph("BULLETIN DE NOTES", self.styles['Title'])
        story.append(title)
        
        # Informations de l'établissement
        ecole_info = [
            ["ÉTABLISSEMENT:", "École SchoolPro"],
            ["ADRESSE:", "123 Avenue de l'Éducation, Yaoundé"],
            ["TÉLÉPHONE:", "+237 123 456 789"],
            ["EMAIL:", "contact@schoolpro.cm"]
        ]
        
        ecole_table = Table(ecole_info, colWidths=[2*inch, 3*inch])
        ecole_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(ecole_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def create_student_info(self, etudiant, classe, trimestre, annee_scolaire):
        """Crée la section informations étudiant"""
        story = []
        
        # Informations personnelles
        info_data = [
            ["Nom:", f"{etudiant.first_name} {etudiant.last_name}"],
            ["Classe:", classe.nom],
            ["Niveau:", classe.get_niveau_display()],
            ["Trimestre:", f"{trimestre}ème Trimestre"],
            ["Année scolaire:", annee_scolaire.annee],
            ["Date de naissance:", etudiant.date_naissance.strftime('%d/%m/%Y')],
            ["Lieu de naissance:", etudiant.lieu_naissance or "Non renseigné"],
            ["Date d'inscription:", etudiant.date_inscription.strftime('%d/%m/%Y')]
        ]
        
        info_table = Table(info_data, colWidths=[1.5*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def create_grades_table(self, etudiant_id, classe, trimestre):
        """Crée le tableau des notes par matière"""
        story = []
        
        # Titre de la section
        subtitle = Paragraph("RÉSULTATS PAR MATIÈRE", self.styles['Subtitle'])
        story.append(subtitle)
        
        # En-tête du tableau
        header = [['Matière', 'Coeff.', 'Moyenne', 'Appréciation']]
        
        # Données des matières
        data = header.copy()
        matieres = classe.matiere.all()
        total_pondere = 0
        total_coeff = 0
        
        for matiere in matieres:
            resultat = calculer_moyenne_etudiant(
                etudiant_id,
                matiere_id=matiere.id,
                trimestre=trimestre
            )
            
            moyenne = resultat['moyenne']
            appreciation = get_appreciation(moyenne)
            
            data.append([
                matiere.nom,
                str(matiere.coefficient),
                f"{moyenne:.2f}" if moyenne > 0 else "N/A",
                appreciation
            ])
            
            if moyenne > 0:
                total_pondere += moyenne * matiere.coefficient
                total_coeff += matiere.coefficient
        
        # Ligne de moyenne générale
        moyenne_generale = total_pondere / total_coeff if total_coeff > 0 else 0
        data.append([
            "MOYENNE GÉNÉRALE",
            str(total_coeff),
            f"{moyenne_generale:.2f}",
            get_appreciation(moyenne_generale)
        ])
        
        # Création du tableau
        grades_table = Table(data, colWidths=[3*inch, 0.8*inch, 1*inch, 1.5*inch])
        grades_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, -2), 10),
            ('FONTSIZE', (0, -1), (-1, -1), 11),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightblue),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(grades_table)
        story.append(Spacer(1, 20))
        
        return story, moyenne_generale
    
    def create_statistics_chart(self, etudiant_id, classe, trimestre):
        """Crée un graphique des statistiques"""
        story = []
        
        # Calcul des moyennes par matière pour le graphique
        matieres_data = []
        moyennes_data = []
        
        for matiere in classe.matiere.all():
            resultat = calculer_moyenne_etudiant(
                etudiant_id,
                matiere_id=matiere.id,
                trimestre=trimestre
            )
            
            if resultat['moyenne'] > 0:
                matieres_data.append(matiere.nom[:10])  # Limiter la longueur
                moyennes_data.append(resultat['moyenne'])
        
        if moyennes_data:
            # Création du graphique en barres
            drawing = Drawing(400, 200)
            
            chart = VerticalBarChart()
            chart.x = 50
            chart.y = 50
            chart.height = 125
            chart.width = 350
            chart.data = [moyennes_data]
            chart.categoryAxis.categoryNames = matieres_data
            chart.categoryAxis.labels.fontSize = 8
            chart.valueAxis.valueMin = 0
            chart.valueAxis.valueMax = 20
            chart.valueAxis.valueStep = 2
            chart.bars[0].fillColor = colors.blue
            chart.bars[0].strokeColor = colors.darkblue
            chart.bars[0].strokeWidth = 1
            
            drawing.add(chart)
            
            # Titre du graphique
            chart_title = Paragraph("ÉVOLUTION DES MOYENNES PAR MATIÈRE", self.styles['Subtitle'])
            story.append(chart_title)
            story.append(drawing)
            story.append(Spacer(1, 20))
        
        return story
    
    def create_ranking_info(self, etudiant_id, classe_id, trimestre, moyenne_generale):
        """Crée la section classement"""
        story = []
        
        # Calcul du rang
        rang = calculer_rang_etudiant(etudiant_id, classe_id, trimestre)
        
        # Statistiques de la classe
        from .utils import calculer_moyenne_classe
        stats_classe = calculer_moyenne_classe(classe_id, trimestre=trimestre)
        
        ranking_data = [
            ["Moyenne générale:", f"{moyenne_generale:.2f}/20"],
            ["Rang dans la classe:", f"{rang}/{stats_classe['nb_etudiants']}"],
            ["Moyenne de la classe:", f"{stats_classe['moyenne_classe']:.2f}/20"],
            ["Effectif de la classe:", str(stats_classe['nb_etudiants'])],
        ]
        
        ranking_table = Table(ranking_data, colWidths=[2*inch, 2*inch])
        ranking_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(ranking_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def create_appreciation(self, moyenne_generale, etudiant, classe):
        """Crée la section appréciation générale"""
        story = []
        
        appreciation = get_appreciation(moyenne_generale)
        
        # Appréciation générale
        appreciation_text = f"""
        <b>APPRÉCIATION GÉNÉRALE :</b><br/>
        {appreciation}<br/><br/>
        
        L'élève {etudiant.first_name} {etudiant.last_name} de la classe {classe.nom} 
        a obtenu une moyenne générale de {moyenne_generale:.2f}/20 au trimestre en cours.
        """
        
        appreciation_para = Paragraph(appreciation_text, self.styles['Info'])
        story.append(appreciation_para)
        story.append(Spacer(1, 20))
        
        return story
    
    def create_footer(self):
        """Crée le pied de page"""
        story = []
        
        footer_data = [
            ["Directeur des Études", "", "Le Responsable de la Classe", ""],
            ["", "", "", ""],
            ["", "", "", ""],
            ["Signature et cachet", "", "Signature et cachet", ""]
        ]
        
        footer_table = Table(footer_data, colWidths=[2*inch, 0.5*inch, 2*inch, 0.5*inch])
        footer_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
            ('LINEBELOW', (0, 3), (0, 3), 1, colors.black),
            ('LINEBELOW', (2, 3), (2, 3), 1, colors.black),
        ]))
        
        story.append(footer_table)
        
        # Date de génération
        date_text = f"Bulletin généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
        date_para = Paragraph(date_text, self.styles['Normal'])
        story.append(date_para)
        
        return story
    
    def generate_bulletin(self, etudiant_id, trimestre, annee_scolaire, include_chart=True):
        """Génère le bulletin complet"""
        try:
            # Récupération des données
            etudiant = Etudiant.objects.get(id=etudiant_id, is_active=True)
            
            # Récupération de la classe
            assignation = etudiant.assignationetudiantclasse_set.filter(
                annee_scolaire=annee_scolaire
            ).first()
            
            if not assignation:
                raise ValueError("Étudiant non assigné à une classe")
            
            classe = assignation.classe
            
            # Création du buffer pour le PDF
            buffer = BytesIO()
            
            # Création du document PDF
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Construction du contenu
            story = []
            
            # En-tête
            story.extend(self.create_header(doc, etudiant, classe, annee_scolaire))
            
            # Informations étudiant
            story.extend(self.create_student_info(etudiant, classe, trimestre, annee_scolaire))
            
            # Tableau des notes
            grades_story, moyenne_generale = self.create_grades_table(etudiant_id, classe, trimestre)
            story.extend(grades_story)
            
            # Graphique (optionnel)
            if include_chart:
                chart_story = self.create_statistics_chart(etudiant_id, classe, trimestre)
                story.extend(chart_story)
            
            # Classement
            ranking_story = self.create_ranking_info(etudiant_id, classe.id, trimestre, moyenne_generale)
            story.extend(ranking_story)
            
            # Appréciation
            appreciation_story = self.create_appreciation(moyenne_generale, etudiant, classe)
            story.extend(appreciation_story)
            
            # Pied de page
            story.extend(self.create_footer())
            
            # Génération du PDF
            doc.build(story)
            
            # Récupération du contenu
            pdf_content = buffer.getvalue()
            buffer.close()
            
            return pdf_content
        
        except Exception as e:
            raise Exception(f"Erreur lors de la génération du bulletin: {str(e)}")


def generate_bulletin_response(etudiant_id, trimestre, annee_scolaire, include_chart=True):
    """Génère une réponse HTTP avec le bulletin PDF"""
    try:
        generator = BulletinPDFGenerator()
        pdf_content = generator.generate_bulletin(etudiant_id, trimestre, annee_scolaire, include_chart)
        
        # Création de la réponse HTTP
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="bulletin_etudiant_{etudiant_id}_trimestre_{trimestre}.pdf"'
        
        return response
    
    except Exception as e:
        return HttpResponse(f"Erreur: {str(e)}", status=500)


def generate_bulletin_file(etudiant_id, trimestre, annee_scolaire, save_path=None):
    """Génère un fichier bulletin et le sauvegarde"""
    try:
        generator = BulletinPDFGenerator()
        pdf_content = generator.generate_bulletin(etudiant_id, trimestre, annee_scolaire)
        
        # Chemin de sauvegarde
        if not save_path:
            filename = f"bulletin_etudiant_{etudiant_id}_trimestre_{trimestre}.pdf"
            save_path = os.path.join(settings.MEDIA_ROOT, 'bulletins', filename)
        
        # Création du dossier si nécessaire
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Sauvegarde du fichier
        with open(save_path, 'wb') as f:
            f.write(pdf_content)
        
        return save_path
    
    except Exception as e:
        raise Exception(f"Erreur lors de la sauvegarde du bulletin: {str(e)}")


# ========== GÉNÉRATEUR DE RAPPORTS DE CLASSE ==========

class RapportClassePDFGenerator:
    """Générateur de rapports de classe PDF"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Configure les styles personnalisés"""
        self.styles.add(ParagraphStyle(
            name='Title',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            alignment=1,
            textColor=colors.darkblue
        ))
    
    def generate_rapport_classe(self, classe_id, trimestre=None):
        """Génère un rapport de classe complet"""
        try:
            from .models import Classe
            from .utils import generer_rapport_classe
            
            classe = Classe.objects.get(id=classe_id)
            rapport_data = generer_rapport_classe(classe_id, trimestre)
            
            # Création du buffer
            buffer = BytesIO()
            
            # Création du document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            story = []
            
            # Titre
            title = Paragraph(f"RAPPORT DE CLASSE - {classe.nom}", self.styles['Title'])
            story.append(title)
            story.append(Spacer(1, 20))
            
            # Tableau des moyennes des étudiants
            if rapport_data.get('statistiques', {}).get('moyennes_etudiants'):
                header = [['Rang', 'Nom de l\'élève', 'Moyenne', 'Nombre de notes']]
                data = header.copy()
                
                for i, etudiant_data in enumerate(rapport_data['statistiques']['moyennes_etudiants'], 1):
                    data.append([
                        str(i),
                        etudiant_data['nom'],
                        f"{etudiant_data['moyenne']:.2f}",
                        str(etudiant_data['nb_notes'])
                    ])
                
                table = Table(data, colWidths=[0.8*inch, 3*inch, 1*inch, 1.2*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                
                story.append(table)
                story.append(Spacer(1, 20))
            
            # Statistiques de la classe
            stats_text = f"""
            <b>STATISTIQUES DE LA CLASSE :</b><br/>
            • Effectif total : {rapport_data['classe']['effectif']}<br/>
            • Moyenne de la classe : {rapport_data['statistiques']['moyenne_classe']:.2f}/20<br/>
            • Nombre d'étudiants avec notes : {rapport_data['statistiques']['nb_etudiants_avec_notes']}<br/>
            """
            
            stats_para = Paragraph(stats_text, self.styles['Normal'])
            story.append(stats_para)
            
            # Génération du PDF
            doc.build(story)
            
            pdf_content = buffer.getvalue()
            buffer.close()
            
            return pdf_content
        
        except Exception as e:
            raise Exception(f"Erreur lors de la génération du rapport: {str(e)}")
