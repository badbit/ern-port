VERSION 4.00
Begin VB.Form Form14 
   BackColor       =   &H00E0E0E0&
   BorderStyle     =   1  'Fixed Single
   Caption         =   "Noti-informa"
   ClientHeight    =   4524
   ClientLeft      =   2112
   ClientTop       =   1224
   ClientWidth     =   5772
   Height          =   4848
   Icon            =   "Form14.frx":0000
   Left            =   2064
   LinkTopic       =   "Form14"
   MaxButton       =   0   'False
   MinButton       =   0   'False
   ScaleHeight     =   4524
   ScaleWidth      =   5772
   Top             =   948
   Width           =   5868
   WindowState     =   2  'Maximized
   Begin VB.CommandButton Command1 
      Caption         =   "Volver al menú principal"
      Height          =   492
      Left            =   6360
      TabIndex        =   8
      Top             =   5520
      Width           =   2172
   End
   Begin VB.Frame Frame1 
      BackColor       =   &H00E0E0E0&
      Caption         =   "Nhoticiaz"
      Height          =   5652
      Left            =   480
      TabIndex        =   1
      Top             =   840
      Width           =   8532
      Begin VB.Label Label7 
         Alignment       =   2  'Center
         BackStyle       =   0  'Transparent
         Caption         =   "Hack-Net.com"
         BeginProperty Font 
            name            =   "Times New Roman"
            charset         =   0
            weight          =   400
            size            =   10.8
            underline       =   0   'False
            italic          =   0   'False
            strikethrough   =   0   'False
         EndProperty
         Height          =   372
         Left            =   5760
         TabIndex        =   7
         Top             =   360
         Width           =   2532
      End
      Begin VB.Label Label6 
         Alignment       =   2  'Center
         BackStyle       =   0  'Transparent
         Caption         =   "Página Hackeada por LoTeK"
         BeginProperty Font 
            name            =   "Times New Roman"
            charset         =   0
            weight          =   400
            size            =   10.8
            underline       =   0   'False
            italic          =   0   'False
            strikethrough   =   0   'False
         EndProperty
         Height          =   372
         Left            =   3000
         TabIndex        =   6
         Top             =   360
         Width           =   2532
      End
      Begin VB.Label Label5 
         Alignment       =   2  'Center
         BackStyle       =   0  'Transparent
         Caption         =   "Juego escondido en Excel '97"
         BeginProperty Font 
            name            =   "Times New Roman"
            charset         =   0
            weight          =   700
            size            =   10.2
            underline       =   0   'False
            italic          =   0   'False
            strikethrough   =   0   'False
         EndProperty
         Height          =   372
         Left            =   240
         TabIndex        =   5
         Top             =   360
         Width           =   2652
      End
      Begin VB.Label Label4 
         BackStyle       =   0  'Transparent
         Caption         =   $"Form14.frx":0442
         BeginProperty Font 
            name            =   "Times New Roman"
            charset         =   0
            weight          =   400
            size            =   9
            underline       =   0   'False
            italic          =   0   'False
            strikethrough   =   0   'False
         EndProperty
         Height          =   3132
         Left            =   5760
         TabIndex        =   4
         Top             =   840
         Width           =   2532
      End
      Begin VB.Label Label3 
         BackStyle       =   0  'Transparent
         Caption         =   $"Form14.frx":05D1
         BeginProperty Font 
            name            =   "Times New Roman"
            charset         =   0
            weight          =   400
            size            =   9
            underline       =   0   'False
            italic          =   0   'False
            strikethrough   =   0   'False
         EndProperty
         Height          =   4212
         Left            =   3000
         TabIndex        =   3
         Top             =   840
         Width           =   2532
      End
      Begin VB.Label Label2 
         BackStyle       =   0  'Transparent
         Caption         =   $"Form14.frx":080F
         BeginProperty Font 
            name            =   "Times New Roman"
            charset         =   0
            weight          =   400
            size            =   9
            underline       =   0   'False
            italic          =   0   'False
            strikethrough   =   0   'False
         EndProperty
         Height          =   4452
         Left            =   240
         TabIndex        =   2
         Top             =   840
         Width           =   2652
      End
   End
   Begin VB.Label Label1 
      Alignment       =   2  'Center
      BackStyle       =   0  'Transparent
      Caption         =   "Noticias"
      BeginProperty Font 
         name            =   "Times New Roman"
         charset         =   0
         weight          =   700
         size            =   19.8
         underline       =   0   'False
         italic          =   0   'False
         strikethrough   =   0   'False
      EndProperty
      Height          =   612
      Left            =   2640
      TabIndex        =   0
      Top             =   120
      Width           =   4092
   End
End
Attribute VB_Name = "Form14"
Attribute VB_Creatable = False
Attribute VB_Exposed = False
Private Sub Command1_Click()
Unload Form14
Form14.Hide
End Sub

Private Sub Label2_Click()

End Sub


Private Sub Label2_DblClick()
MsgBox ("Para entrar al juego de Excel '95: Entrar a Excel, Irse a la línea 95, presionar el número que nos indica la línea, presionar TAB, entrar a Ayuda = Help, Seleccionar 'Acerca de Microsoft Excel', mantener presionados Ctrl+Alt+Shift y presionar el botón de Soporte técnico"), , "Lo encontraste"
End Sub


