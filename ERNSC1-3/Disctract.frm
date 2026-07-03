VERSION 4.00
Begin VB.Form Disctract 
   Caption         =   "Reporte Anual de Ventas"
   ClientHeight    =   4524
   ClientLeft      =   912
   ClientTop       =   1464
   ClientWidth     =   5772
   Height          =   5076
   Icon            =   "Disctract.frx":0000
   Left            =   864
   LinkTopic       =   "Form19"
   ScaleHeight     =   4524
   ScaleWidth      =   5772
   Top             =   960
   Width           =   5868
   WindowState     =   2  'Maximized
   Begin VB.CommandButton Command3 
      Caption         =   "S"
      BeginProperty Font 
         name            =   "MS Sans Serif"
         charset         =   0
         weight          =   400
         size            =   7.8
         underline       =   -1  'True
         italic          =   0   'False
         strikethrough   =   0   'False
      EndProperty
      Height          =   252
      Left            =   3840
      TabIndex        =   15
      Top             =   120
      Width           =   252
   End
   Begin VB.CommandButton Command2 
      Caption         =   "C"
      BeginProperty Font 
         name            =   "MS Sans Serif"
         charset         =   0
         weight          =   400
         size            =   7.8
         underline       =   0   'False
         italic          =   -1  'True
         strikethrough   =   0   'False
      EndProperty
      Height          =   252
      Left            =   3600
      TabIndex        =   14
      Top             =   120
      Width           =   252
   End
   Begin VB.CommandButton Command1 
      Caption         =   "N"
      BeginProperty Font 
         name            =   "MS Sans Serif"
         charset         =   0
         weight          =   700
         size            =   7.8
         underline       =   0   'False
         italic          =   0   'False
         strikethrough   =   0   'False
      EndProperty
      Height          =   252
      Left            =   3360
      TabIndex        =   13
      Top             =   120
      Width           =   252
   End
   Begin VB.OptionButton Option4 
      Caption         =   "Justificado"
      Height          =   252
      Left            =   3120
      TabIndex        =   12
      Top             =   600
      Width           =   1092
   End
   Begin VB.OptionButton Option3 
      Caption         =   "Derecha"
      Height          =   252
      Left            =   2160
      TabIndex        =   11
      Top             =   600
      Width           =   1092
   End
   Begin VB.OptionButton Option2 
      Caption         =   "Centrado"
      Height          =   252
      Left            =   1080
      TabIndex        =   10
      Top             =   600
      Width           =   1212
   End
   Begin VB.OptionButton Option1 
      Caption         =   "Izquierda"
      Height          =   252
      Left            =   120
      TabIndex        =   9
      Top             =   600
      Width           =   1092
   End
   Begin VB.TextBox Text2 
      Height          =   288
      Left            =   6360
      TabIndex        =   8
      Text            =   "Introduzca su nombre"
      Top             =   600
      Width           =   3012
   End
   Begin VB.CommandButton Command6 
      Caption         =   "Nuevo"
      Height          =   252
      Left            =   7200
      TabIndex        =   7
      Top             =   120
      Width           =   1092
   End
   Begin VB.CommandButton Command5 
      Caption         =   "Abrir"
      Height          =   252
      Left            =   6000
      TabIndex        =   6
      Top             =   120
      Width           =   1092
   End
   Begin VB.CommandButton Command4 
      Caption         =   "Guardar"
      Height          =   252
      Left            =   4920
      TabIndex        =   5
      Top             =   120
      Width           =   972
   End
   Begin VB.ComboBox Combo2 
      Height          =   288
      Left            =   2640
      TabIndex        =   4
      Text            =   "14"
      Top             =   120
      Width           =   492
   End
   Begin VB.ComboBox Combo1 
      Height          =   288
      Left            =   96
      TabIndex        =   3
      Text            =   "Times new roman"
      Top             =   120
      Width           =   2412
   End
   Begin VB.HScrollBar HScroll1 
      Height          =   216
      Left            =   0
      TabIndex        =   2
      Top             =   6240
      Width           =   9372
   End
   Begin VB.VScrollBar VScroll1 
      Height          =   5184
      Left            =   9360
      TabIndex        =   1
      Top             =   948
      Width           =   216
   End
   Begin VB.TextBox Text1 
      BeginProperty Font 
         name            =   "Times New Roman"
         charset         =   0
         weight          =   400
         size            =   12
         underline       =   0   'False
         italic          =   0   'False
         strikethrough   =   0   'False
      EndProperty
      Height          =   5292
      Left            =   0
      Locked          =   -1  'True
      MultiLine       =   -1  'True
      TabIndex        =   0
      Text            =   "Disctract.frx":0442
      Top             =   960
      Width           =   9372
   End
   Begin VB.Shape Shape1 
      Height          =   492
      Left            =   0
      Top             =   0
      Width           =   9612
   End
   Begin VB.Menu fil 
      Caption         =   "&Archivo"
      Begin VB.Menu esde 
         Caption         =   "&Salir"
         Shortcut        =   ^S
      End
   End
   Begin VB.Menu ed 
      Caption         =   "&Edición"
   End
   Begin VB.Menu see 
      Caption         =   "&Ver"
   End
   Begin VB.Menu dfffged 
      Caption         =   "&Ir a"
   End
   Begin VB.Menu sffef 
      Caption         =   "&Herramientas"
   End
   Begin VB.Menu fdfdsf 
      Caption         =   "&Opciones"
   End
   Begin VB.Menu fdsf 
      Caption         =   "A&yuda"
   End
End
Attribute VB_Name = "Disctract"
Attribute VB_Creatable = False
Attribute VB_Exposed = False
Private Sub esde_Click()
Unload Distract
Distract.Hide
End Sub


