#Read XMP Metadata

Vous pouvez choisir Custom et lire les types suivants :
- XMP standards (XMP-dc:)

Creator</br>
Rights</br>
Title</br>
Contributor</br>
Coverage</br>
Date</br>
Format</br>
Identifier</br>
Language</br>
Publisher</br>
Relation</br>
Source</br>
Type</br>

- Autres noms XMP </br>
Pour ceux-là, il faudra inclure le préfixe entier :

XMP-xmp:CreateDate - Date de création </br>
XMP-xmp:ModifyDate - Date de modification  </br>
XMP-xmp:CreatorTool - Outil de création	</br>
XMP-xmp:Rating - Note/évaluation </br>
XMP-photoshop:City - Ville </br>
XMP-photoshop:Country - Pays </br>
XMP-photoshop:Credit - Crédit </br>
XMP-photoshop:Headline - Titre principal </br>
XMP-photoshop:Instructions - Instructions </br>
XMP-iptcCore:Keywords - Mots-clés IPTC </br>

Exemples :

✅ Creator → XMP-dc:Creator</br>
✅ Rights → XMP-dc:Rights</br>
✅ XMP-xmp:Rating → XMP-xmp:Rating</br>
✅ XMP-photoshop:City → XMP-photoshop:City</br>

❌ Comment (pas un champ XMP standard)</br>
❌ Azerty (nom inventé)</br>
❌ Author (utilisez Creator à la place)</br>