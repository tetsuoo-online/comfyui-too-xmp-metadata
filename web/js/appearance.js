import { app } from "../../../../scripts/app.js";

// Extension pour appliquer des couleurs personnalisées aux nœuds comfyui-too-xmp-metadata
app.registerExtension({
    name: "comfyui-too-xmp-metadata.appearance",
    async setup() {
        console.log("ComfyUI Too XMP Metadata appearance extension setup");
    },
    
    async beforeRegisterNodeDef(nodeType, nodeData) {
        // Vérifier si le nœud appartient à comfyui-too-xmp-metadata
        if (nodeData.category && nodeData.category.startsWith("too")) {
            console.log(`Found ComfyUI Too XMP Metadata Node: ${nodeData.name}, applying custom colors`);
            
            // Définition des couleurs
            const backgroundColor = "#2E3B4E";  // Bleu foncé
            const titleColor = "#FF0000";  //doesn't work
            const textColor = "#BABACC";

            // Sauvegarder la fonction originale onNodeCreated
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            
            // Modifier la fonction onNodeCreated
            nodeType.prototype.onNodeCreated = function() {
                if (onNodeCreated) {
                    onNodeCreated.apply(this, arguments);
                }
                
                // Appliquer les couleurs personnalisées
                this.bgcolor = backgroundColor;
                this.color = textColor;

                // Sauvegarder la fonction originale drawTitleBar
                const originalDrawTitleBar = this.drawTitleBar;
                
                // Modifier drawTitleBar pour utiliser la couleur du titre
                this.drawTitleBar = function(ctx, title_height) {
                    originalDrawTitleBar.call(this, ctx, title_height);
                    
                    if (this.flags.collapsed) {
                        return;
                    }

                    // Custom title color
                    ctx.save();
                    ctx.fillStyle = titleColor; // Apply custom color
                    ctx.font = this.title_font || LiteGraph.DEFAULT_TITLE_FONT;

                    const title = this.getTitle();
                    if (title) {
                        // Draw the title text with custom color
                        ctx.fillText(title, 10, title_height * 0.75);
                    }

                    ctx.restore();
                };

                console.log(`Applied custom colors to ComfyUI Too XMP Metadata Node: ${this.type}`);
            };
        }
    }
});
