VERSION 4.00
Begin VB.Form Form2 
   BackColor       =   &H00C0C0C0&
   BorderStyle     =   1  'Fixed Single
   Caption         =   "Resumen"
   ClientHeight    =   6360
   ClientLeft      =   192
   ClientTop       =   240
   ClientWidth     =   9336
   Height          =   6684
   Icon            =   "Form2.frx":0000
   Left            =   144
   LinkTopic       =   "Form2"
   MaxButton       =   0   'False
   MinButton       =   0   'False
   ScaleHeight     =   6360
   ScaleWidth      =   9336
   ShowInTaskbar   =   0   'False
   Top             =   -36
   Width           =   9432
   WindowState     =   2  'Maximized
   Begin VB.Frame Frame1 
      BackColor       =   &H00C0C0C0&
      Caption         =   "Contenido"
      ForeColor       =   &H000000FF&
      Height          =   4932
      Left            =   240
      TabIndex        =   1
      Top             =   1200
      Width           =   9132
      Begin VB.CommandButton Command7 
         Caption         =   "Volver al menú principal"
         Height          =   372
         Left            =   120
         TabIndex        =   7
         Top             =   4200
         Width           =   2172
      End
      Begin VB.Label Label7 
         BackStyle       =   0  'Transparent
         Caption         =   "           BadBit está próximo a sacar el BadBit's Credit Card Number Validator v1.5, espérenlo en su dirección."
         ForeColor       =   &H00000000&
         Height          =   972
         Left            =   240
         TabIndex        =   9
         Top             =   3480
         Width           =   8652
      End
      Begin VB.Label Label6 
         BackStyle       =   0  'Transparent
         Caption         =   $"Form2.frx":0442
         ForeColor       =   &H00000000&
         Height          =   972
         Left            =   240
         TabIndex        =   8
         Top             =   2760
         Width           =   8652
      End
      Begin VB.Label Label5 
         BackColor       =   &H00808080&
         BackStyle       =   0  'Transparent
         Caption         =   "http://www.bigfoot.com/~ernt"
         BeginProperty Font 
            name            =   "Courier New"
            charset         =   0
            weight          =   400
            size            =   10.2
            underline       =   0   'False
            italic          =   0   'False
            strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00000000&
         Height          =   372
         Left            =   240
         TabIndex        =   6
         Top             =   2280
         Width           =   8172
      End
      Begin VB.Label Label4 
         AutoSize        =   -1  'True
         BackStyle       =   0  'Transparent
         Caption         =   "Y la de BadBit:"
         ForeColor       =   &H00000000&
         Height          =   192
         Left            =   840
         TabIndex        =   5
         Top             =   1920
         Width           =   1056
      End
      Begin VB.Label Label3 
         BackColor       =   &H00808080&
         BackStyle       =   0  'Transparent
         Caption         =   "http://www.angelfire.com/il/radiaktivonews/radiactivo.html"
         BeginProperty Font 
            name            =   "Courier New"
            charset         =   0
            weight          =   400
            size            =   10.2
            underline       =   0   'False
            italic          =   0   'False
            strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00000000&
         Height          =   372
         Left            =   240
         TabIndex        =   4
         Top             =   1560
         Width           =   8172
      End
      Begin VB.Label Label1 
         BackStyle       =   0  'Transparent
         Caption         =   $"Form2.frx":0564
         ForeColor       =   &H00000000&
         Height          =   612
         Left            =   240
         TabIndex        =   3
         Top             =   840
         Width           =   8412
      End
      Begin VB.Label Label2 
         BackColor       =   &H00808080&
         BackStyle       =   0  'Transparent
         Caption         =   $"Form2.frx":0600
         ForeColor       =   &H00000000&
         Height          =   492
         Left            =   240
         TabIndex        =   2
         Top             =   360
         Width           =   8292
      End
   End
   Begin VB.Label Título 
      Alignment       =   2  'Center
      BackColor       =   &H00000000&
      Caption         =   "Novedades"
      BeginProperty Font 
         name            =   "Arial Black"
         charset         =   0
         weight          =   400
         size            =   18
         underline       =   0   'False
         italic          =   0   'False
         strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H00FF0000&
      Height          =   612
      Left            =   2160
      TabIndex        =   0
      Top             =   360
      Width           =   5532
   End
End
Attribute VB_Name = "Form2"
Attribute VB_Creatable = False
Attribute VB_Exposed = False
Private Sub Command1_Click()
Load Form3
Form3.Show
Unload Form2
Form2.Hide
End Sub

Private Sub Command2_Click()
Load Form4
Form4.Show
Unload Form2
Form2.Hide
End Sub


Private Sub Command3_Click()
Load Form6
Form6.Show
Unload Form2
Form2.Hide
End Sub


Private Sub Command4_Click()
Load Form13
Form13.Show
Unload Form2
Form2.Hide
End Sub


Private Sub Command5_Click()
Load Form14
Form14.Show
Unload Form2
Form2.Hide
End Sub


Private Sub Command6_Click()
Load Form17
Form17.Show
Unload Form2
Form2.Show
End Sub

Private Sub Command7_Click()
Unload Form2
Form2.Hide
End Sub

Private Sub Command8_Click()
Load Form15
Form15.Show
Unload Form2
Form2.Hide
End Sub


Private Sub Label8_Click()

End Sub


