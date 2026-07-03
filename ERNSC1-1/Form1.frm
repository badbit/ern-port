VERSION 4.00
Begin VB.Form Form1 
   BackColor       =   &H00800000&
   BorderStyle     =   1  'Fixed Single
   Caption         =   "BadBit presenta: EL Radiactivo News"
   ClientHeight    =   4524
   ClientLeft      =   1584
   ClientTop       =   1776
   ClientWidth     =   6552
   Height          =   5076
   Icon            =   "Form1.frx":0000
   Left            =   1536
   LinkTopic       =   "Form1"
   MaxButton       =   0   'False
   MinButton       =   0   'False
   Picture         =   "Form1.frx":0442
   ScaleHeight     =   4524
   ScaleWidth      =   6552
   Top             =   1272
   WhatsThisButton =   -1  'True
   WhatsThisHelp   =   -1  'True
   Width           =   6648
   Begin VB.CommandButton Command3 
      Caption         =   "Haz click si no tienes nada que hacer"
      Height          =   495
      Left            =   600
      TabIndex        =   4
      Top             =   3840
      Width           =   1935
   End
   Begin VB.CommandButton Command2 
      Caption         =   "Salir"
      Height          =   375
      Left            =   4920
      TabIndex        =   3
      Top             =   3960
      Width           =   1455
   End
   Begin VB.CommandButton Command1 
      Caption         =   "Aclaración"
      Height          =   375
      Left            =   3120
      TabIndex        =   2
      Top             =   3960
      Width           =   1575
   End
   Begin VB.Label Label3 
      BackStyle       =   0  'Transparent
      Caption         =   "Año I, número 1, Agosto 1998."
      ForeColor       =   &H00FFFFFF&
      Height          =   612
      Left            =   5040
      TabIndex        =   5
      Top             =   720
      Width           =   1452
   End
   Begin VB.Label Label2 
      AutoSize        =   -1  'True
      BackColor       =   &H00FFFFFF&
      BorderStyle     =   1  'Fixed Single
      Caption         =   $"Form1.frx":0A66
      ForeColor       =   &H00FF0000&
      Height          =   2172
      Left            =   360
      TabIndex        =   1
      Top             =   840
      Width           =   3384
      WordWrap        =   -1  'True
   End
   Begin VB.Label Label1 
      Alignment       =   2  'Center
      BackStyle       =   0  'Transparent
      Caption         =   "El Radiactivo News"
      BeginProperty Font 
         name            =   "MS Sans Serif"
         charset         =   0
         weight          =   400
         size            =   18
         underline       =   0   'False
         italic          =   0   'False
         strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H000000FF&
      Height          =   492
      Left            =   720
      TabIndex        =   0
      Top             =   120
      Width           =   4812
   End
   Begin VB.Menu file 
      Caption         =   "&Archivo"
      Index           =   1
      WindowList      =   -1  'True
      Begin VB.Menu files 
         Caption         =   "Archivos incluidos"
      End
      Begin VB.Menu separ 
         Caption         =   "-"
      End
      Begin VB.Menu exit 
         Caption         =   "Salir"
         Shortcut        =   ^Q
      End
   End
   Begin VB.Menu articles 
      Caption         =   "A&rtículos"
      Begin VB.Menu index 
         Caption         =   "Indice"
      End
      Begin VB.Menu sep3 
         Caption         =   "-"
      End
      Begin VB.Menu editor 
         Caption         =   "Editorial"
      End
      Begin VB.Menu welcome 
         Caption         =   "Bienvenidos"
      End
      Begin VB.Menu hacker 
         Caption         =   "¿Qué es un hacker?"
      End
      Begin VB.Menu history 
         Caption         =   "Un poco de historia"
      End
      Begin VB.Menu news 
         Caption         =   "Ultimas noticias"
      End
      Begin VB.Menu col 
         Caption         =   "Columnas"
         Begin VB.Menu binary 
            Caption         =   "Perdidos en el cyberespacio"
         End
      End
      Begin VB.Menu next 
         Caption         =   "En el próximo número"
      End
   End
   Begin VB.Menu utils 
      Caption         =   "&Utilidades"
      Begin VB.Menu clock 
         Caption         =   "Reloj"
      End
      Begin VB.Menu screen 
         Caption         =   "Pantalla distractora"
         Shortcut        =   {F5}
      End
   End
   Begin VB.Menu help 
      Caption         =   "A&yuda"
      Begin VB.Menu contents 
         Caption         =   "Contenido"
      End
      Begin VB.Menu credits 
         Caption         =   "Créditos"
      End
      Begin VB.Menu contactus 
         Caption         =   "Cómo contactarnos"
      End
      Begin VB.Menu sep1 
         Caption         =   "-"
      End
      Begin VB.Menu about 
         Caption         =   "Acerca de ""El Radiactivo News"""
      End
   End
End
Attribute VB_Name = "Form1"
Attribute VB_Creatable = False
Attribute VB_Exposed = False
Private Sub about_Click()
Load Acerca
Acerca.Show
End Sub

Private Sub binary_Click()
Load Form15
Form15.Show
End Sub


Private Sub clock_Click()
Load Reloj
Reloj.Show
End Sub

Private Sub Command1_Click()
Load Aclaración
Aclaración.Show
End Sub

Private Sub Command2_Click()
End
End Sub

Private Sub Command3_Click()
clave = InputBox("Introduce tu password", "Ja!")
If clave = "5422652" Then
    MsgBox ("Le atinaste")
Else
    MsgBox ("No le atinaste"), , "Otra vez Ja!"
End If
End Sub

Private Sub contactus_Click()
Load Form17
Form17.Show
End Sub

Private Sub contents_Click()
Load Ayuda
Ayuda.Show
End Sub

Private Sub credits_Click()
Load Form16
Form16.Show
End Sub

Private Sub editor_Click()
Load Form3
Form3.Show
End Sub

Private Sub exit_Click()
End
End Sub

Private Sub files_Click()
Load Form18
Form18.Show
End Sub

Private Sub Form_Load()
MsgBox ("El Radiactivo News"), , "Advertencia"
End Sub


Private Sub hacker_Click()
Load Form6
Form6.Show
End Sub

Private Sub history_Click()
Load Form13
Form13.Show
End Sub

Private Sub index_Click()
Load Form2
Form2.Show
End Sub

Private Sub news_Click()
Load Form14
Form14.Show
End Sub

Private Sub next_Click()
Load Form19
Form19.Show
End Sub

Private Sub screen_Click()
Load Disctract
Disctract.Show
End Sub

Private Sub welcome_Click()
Load Form4
Form4.Show
End Sub


