from tkinter import Tk, Button, Scale, Canvas, Label, StringVar, Entry, \
    Toplevel, messagebox, filedialog
from tkinter.colorchooser import askcolor
from PIL import Image, ImageTk
import os
import time

"""////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
Pour faire fonctionner le code il faut impérativement télécharger : 
- Pillow (package pip) 
- GhostScript et l'ajouté au variable 'Path' de windows 

Ce code est une tentative de répliquer le logiciel 'Paint'.
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////"""




class FilenamePopup:

    #Création d' une fenêtre popup à partir d'une fenêtre parent 'master' (ici de l'élément Paint).
    #La fenêtre popup contient un label pour demander à l'utilisateur de choisir un nom de fichier,
    #une zone de texte pour saisir le nom de fichier et un bouton "Ok" pour valider le choix et fermer la fenêtre popup.
    def __init__(self, master):
        top = self.top = Toplevel(master)
        self.lbl = Label(top, text="Choisissez le nom de fichier : ")
        self.lbl.pack()
        self.ent_filename = Entry(top)
        self.ent_filename.pack()
        self.btn_ok = Button(top, text='Ok', command=self.cleanup)
        self.btn_ok.pack()

    def cleanup(self):
        self.filename = self.ent_filename.get()
        self.top.destroy()


class Paint(object):

    """
    L'application dispose d'outils tels que le stylo, le pinceau, la gomme,la ligne et le polygone pour dessiner sur une toile.
    L'utilisateur peut également choisir la couleur et la taille de la brosse.
    L'interface utilisateur contient des boutons pour chaque outil,
    ainsi qu'un écran pour afficher les informations sur l'outil sélectionné et la couleur actuelle.

    """

    #Déclaration des valeurs de bases
    DEFAULT_PEN_SIZE = 5.0
    DEFAULT_COLOR = 'black'
    color = DEFAULT_COLOR


    def __init__(self):

        #Déclaration des boutons et des valeurs de bases du canva et de la fenêtre.

        self.DisplayImg = None
        self.root = Tk()
        self.root.title("Éditeur d'image matricielle")

        self.pen_button = Button(self.root, text='Stylo', command=self.use_pen)
        self.pen_button.grid(row=0, column=0, sticky="ew")

        self.brush_button = Button(self.root, text='Pinceau',
                                   command=self.use_brush)
        self.brush_button.grid(row=0, column=1, sticky="ew")

        self.color_button = Button(self.root, text='Choix Couleur',
                                   command=self.choose_color)
        self.color_button.grid(row=0, column=2, sticky="ew")

        self.eraser_button = Button(self.root, text='Effaceur',
                                    command=self.use_eraser)
        self.eraser_button.grid(row=0, column=3, sticky="ew")

        self.size_scale = Scale(self.root, from_=1, to=10,
                                orient='horizontal')
        self.size_scale.grid(row=0, column=5, sticky="ew")

        self.choix = Button(self.root, text='Choix de la taille :',
                            command="")
        self.choix.grid(row=0, column=4, sticky="ew")

        self.line_button = Button(self.root, text='Ligne',
                                  command=self.use_line)
        self.line_button.grid(row=1, column=0, sticky="ew")

        self.poly_button = Button(self.root, text='Polygone',
                                  command=self.use_poly)
        self.poly_button.grid(row=1, column=1, sticky="ew")

        self.black_button = Button(self.root, text='', bg="black",
                                   activebackground="black",
                                   command="")
        self.black_button.grid(row=1, column=2, sticky="ew")

        self.clear_button = Button(self.root, text='Effacer',
                                   command=lambda: self.c.delete("all"))
        self.clear_button.grid(row=1, column=3, sticky="ew")

        self.save_button = Button(self.root, text="Sauvegarder",
                                  command=self.save_file)
        self.save_button.grid(row=1, column=4, sticky="ew")

        self.file_button = Button(self.root, text="Ouvrir un fichier",
                                  command=self.open_file)
        self.file_button.grid(row=1, column=5, sticky="ew")

        # Déclaration de la fnètre
        self.c = Canvas(self.root, bg='white', width=1200, height=800)
        self.c.grid(row=2, columnspan=6)

        # Déclaration du statues de la sélection (ici de base)
        self.var_status = StringVar(value="Sélection : Stylo")
        self.lbl_status = Label(self.root, textvariable=self.var_status)
        self.lbl_status.grid(row=4, column=5, rowspan=3)

        self.setup()
        self.root.mainloop()

    def setup(self):
        #Déclaration des valeurs des variables de bases et assignation des touches
        self.old_x, self.old_y = None, None
        self.color = self.DEFAULT_COLOR
        self.eraser_on = False
        self.active_button = None
        self.size_multiplier = 1

        self.activate_button(self.pen_button)
        self.c.bind('<B1-Motion>', self.paint)
        self.c.bind('<ButtonRelease-1>', self.reset)

        self.c.bind('<Button-1>', self.point)
        self.root.bind('<Escape>', self.line_reset)
        self.line_start = (None, None)

    def use_pen(self):
        #active le bouton stylo et définie le multiplicateur de pixel à 1 (c'est un stylo, donc il est petit)
        self.activate_button(self.pen_button)
        self.size_multiplier = 1

    def use_brush(self):
        #active le bouton pinceau et définie le multiplicateur de pixel à 2.5 (c'est un pinceau, donc il est plus gros)
        self.activate_button(self.brush_button)
        self.size_multiplier = 2.5

    def use_line(self):
        #active le buton Ligne de l'interface
        self.activate_button(self.line_button)

    def use_poly(self):
        #active le bouton polygone de l'interface
        self.activate_button(self.poly_button)

    def choose_color(self):
        #Choisie la couleur de l'écriture et l'affiche sur l'interface
        self.eraser_on = False
        color = askcolor(color=self.color)[1]
        if color is not None:
            self.color = color
            self.black_button.configure(bg=color, activebackground=color)

    def use_eraser(self):
        #active le boutun Effaceur de l'interface
        self.activate_button(self.eraser_button, eraser_mode=True)

    def activate_button(self, some_button, eraser_mode=False):
        #La méthode activate_button est utilisée pour définir l'état des différents boutons.
        #Elle est appelée lorsqu'un bouton est cliqué et met à jour l'état des boutons pour refléter l'outil actuellement sélectionné.
        self.set_status()
        if self.active_button:
            self.active_button.config(relief='raised')
        some_button.config(relief='sunken')
        self.active_button = some_button
        self.eraser_on = eraser_mode

    def paint(self, event):
        #La méthode paint est la méthode qui prend en paramètre ce qui se passe sur le canva et permet le "dessin" dessus.
        #Elle prend en compte les multiplicateurs pour modifier à l'affichage selon le bouton cocher.
        self.set_status(event.x, event.y)
        line_width = self.size_scale.get() * self.size_multiplier
        paint_color = 'white' if self.eraser_on else self.color
        if self.old_x and self.old_y:
            self.c.create_line(self.old_x, self.old_y, event.x, event.y,
                               width=line_width, fill=paint_color,
                               capstyle='round', smooth=True, splinesteps=36)
        self.old_x = event.x
        self.old_y = event.y

    def line(self, x, y):
        #La méthode permet la création de ligne à partir du dernier endroit cliquer jusqu'au prochain clic.
        line_width = self.size_scale.get() * self.size_multiplier
        paint_color = 'white' if self.eraser_on else self.color
        self.c.create_line(self.line_start[0], self.line_start[1], x, y,
                           width=line_width, fill=paint_color,
                           capstyle='round', smooth=True, splinesteps=36)

    def point(self, event):
        #La méthode permet de récupérer les valeurs du clic sur le canva, l'endroit où l'utilisateur à cliquer
        self.set_status(event.x, event.y)
        btn = self.active_button["text"]
        if btn in ("Ligne", "Polygone"):
            self.size_multiplier = 1
            if any(self.line_start):
                self.line(event.x, event.y)
                self.line_start = ((None, None) if btn == 'Ligne'
                                   else (event.x, event.y))
            else:
                self.line_start = (event.x, event.y)

    def reset(self, event):
        #Stop l'enregistrement des mouvements après que l'utilisateur est lâché le bouton
        self.old_x, self.old_y = None, None

    def line_reset(self, event):
        #Mets en pause l'enregistrement des lignes après que la dernière ligne est étée posée
        self.line_start = (None, None)

    def color_default(self):
        #Méthode qui récupère la couleur par défault
        self.color = self.DEFAULT_COLOR

    def set_status(self, x=None, y=None):
        #Méthode permettant l'affichage des événements en bas à droite de la fenêtre
        if self.active_button:
            btn = self.active_button["text"]
            oldxy = (self.line_start if btn in ("Ligne", "Polygone")
                     else (self.old_x, self.old_y))

            self.var_status.set(f"Sélection : {btn}\n" +
                                (f"Ancien (x, y): {oldxy}\n Actuel (x, y): ({x}, {y})"
                                 if x is not None and y is not None else ""))

    def save_file(self):
        #Permets l'enregistrement des fichées
        self.popup = FilenamePopup(self.root)
        self.save_button["state"] = "disabled"
        self.root.wait_window(self.popup.top)

        filepng = self.popup.filename + '.png'

        if not os.path.exists("C:\\Users\\Noah\\Pictures\paint\\" + filepng) or \
                messagebox.askyesno("File already exists", "Overwrite?"):
            fileps = "C:\\Users\\Noah\\Pictures\\paint\\" + self.popup.filename + '.eps'

            self.c.postscript(file=fileps)
            img = Image.open(fileps)
            img.save("C:\\Users\\Noah\\Pictures\paint\\" + filepng, 'png')
            img.close()

            os.remove(fileps)

            self.save_button["state"] = "normal"

            messagebox.showinfo("Fichier sauvegardé", "Fichier sauvegardé !")
        else:
            messagebox.showwarning("Fichier sauvegardé", "Fichier non sauvegardé")
        self.save_button["state"] = "normal"

    def open_file(self):
        #Permets l'ouverture et l'affichage d'un fichier présent sur l'ordinateur
        filename = filedialog.askopenfilename(initialdir="C:\\Users\\Noah\\Pictures\\paint",
                                              title="Choisissez un fichier",
                                              filetypes=(("",
                                                          "*"),
                                                         ("all files",
                                                          "*.*")))
        img = Image.open(filename)
        self.img_width, self.img_height = img.size
        img = img.resize((self.img_width, self.img_height), Image.LANCZOS)
        self.img_tk = ImageTk.PhotoImage(img)
        self.c = Canvas(self.root, width=self.img_width, height=self.img_height)
        self.c.grid(row=2, columnspan=6)
        self.c.create_image(0, 0, anchor="nw", image=self.img_tk)
        self.setup()
        self.root.mainloop()
        
if __name__ == '__main__':
    Paint()