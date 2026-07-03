VERSION 4.00
Begin VB.Form Form17 
   BackColor       =   &H00000000&
   Caption         =   "Sección Negra - El Radiaktivo Newz"
   ClientHeight    =   5232
   ClientLeft      =   216
   ClientTop       =   1176
   ClientWidth     =   9216
   Height          =   5556
   Icon            =   "Form17.frx":0000
   Left            =   168
   LinkTopic       =   "Form17"
   ScaleHeight     =   5232
   ScaleWidth      =   9216
   Top             =   900
   Width           =   9312
   Begin VB.CommandButton Command1 
      Caption         =   "Cerrar sección negra"
      Height          =   372
      Left            =   4440
      TabIndex        =   4
      Top             =   4560
      Width           =   4452
   End
   Begin VB.Image Image1 
      BorderStyle     =   1  'Fixed Single
      Height          =   1044
      Left            =   1800
      Picture         =   "Form17.frx":0442
      Top             =   120
      Width           =   5448
   End
   Begin VB.Label Label10 
      BackStyle       =   0  'Transparent
      Caption         =   "Puedes bajarla de: http://ernt.piratas.org"
      BeginProperty Font {0BE35203-8F91-11CE-9DE3-00AA004BB851} 
         Name            =   "Fixedsys"
         Size            =   10.8
         Charset         =   0
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H00FFFFFF&
      Height          =   492
      Left            =   360
      TabIndex        =   7
      Top             =   3960
      Width           =   3612
   End
   Begin VB.Label Label9 
      BackStyle       =   0  'Transparent
      Caption         =   "El Radiaktivo Newz Team en Bigfoot punto com"
      ForeColor       =   &H00E0E0E0&
      Height          =   372
      Left            =   360
      TabIndex        =   6
      Top             =   3600
      Width           =   3732
   End
   Begin VB.Label Label5 
      BackStyle       =   0  'Transparent
      Caption         =   "ernt@bigfoot.com"
      BeginProperty Font {0BE35203-8F91-11CE-9DE3-00AA004BB851} 
         Name            =   "Fixedsys"
         Size            =   10.8
         Charset         =   0
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H00FFFFFF&
      Height          =   372
      Left            =   480
      TabIndex        =   5
      Top             =   3240
      Width           =   2772
   End
   Begin VB.Label Label7 
      BackColor       =   &H00000000&
      BackStyle       =   0  'Transparent
      Caption         =   $"Form17.frx":9B10
      BeginProperty Font {0BE35203-8F91-11CE-9DE3-00AA004BB851} 
         Name            =   "Courier New"
         Size            =   10.2
         Charset         =   0
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H00FFFFFF&
      Height          =   1932
      Left            =   4560
      TabIndex        =   3
      Top             =   2400
      Width           =   4212
   End
   Begin VB.Label Label6 
      Alignment       =   2  'Center
      BackStyle       =   0  'Transparent
      Caption         =   "El Radiaktivo Newz otra vez solicita aliados."
      BeginProperty Font {0BE35203-8F91-11CE-9DE3-00AA004BB851} 
         Name            =   "Arial"
         Size            =   10.8
         Charset         =   0
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H000000FF&
      Height          =   612
      Left            =   4680
      TabIndex        =   2
      Top             =   1800
      Width           =   4092
   End
   Begin VB.Label Label4 
      BackStyle       =   0  'Transparent
      Caption         =   "Para contactar a El Radiaktivo Newz Team puedes mandar un correo electrónico a:"
      BeginProperty Font {0BE35203-8F91-11CE-9DE3-00AA004BB851} 
         Name            =   "MS Sans Serif"
         Size            =   12
         Charset         =   0
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H00FFFFFF&
      Height          =   1092
      Left            =   480
      TabIndex        =   1
      Top             =   2160
      Width           =   3492
   End
   Begin VB.Label Label3 
      Alignment       =   2  'Center
      BackColor       =   &H00000000&
      BackStyle       =   0  'Transparent
      Caption         =   "El Radiaktivo Newz"
      BeginProperty Font {0BE35203-8F91-11CE-9DE3-00AA004BB851} 
         Name            =   "Fixedsys"
         Size            =   10.8
         Charset         =   0
         Weight          =   400
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H00FFFFFF&
      Height          =   372
      Left            =   840
      TabIndex        =   0
      Top             =   1800
      Width           =   2772
   End
   Begin VB.Shape Shape1 
      BorderColor     =   &H000000FF&
      BorderWidth     =   4
      Height          =   3252
      Left            =   240
      Shape           =   4  'Rounded Rectangle
      Top             =   1680
      Width           =   3972
   End
   Begin VB.Shape Shape2 
      BorderColor     =   &H00FFFFFF&
      BorderWidth     =   5
      Height          =   2772
      Left            =   4440
      Shape           =   4  'Rounded Rectangle
      Top             =   1680
      Width           =   4452
   End
End
Attribute VB_Name = "Form17"
Attribute VB_Creatable = False
Attribute VB_Exposed = False

Private Sub Command1_Click()
Unload Form17
Form17.Hide
End Sub


