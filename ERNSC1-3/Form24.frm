VERSION 4.00
Begin VB.Form Form24 
   BackColor       =   &H00000000&
   Caption         =   "Revisión de software: Windows 98"
   ClientHeight    =   4524
   ClientLeft      =   912
   ClientTop       =   1236
   ClientWidth     =   5772
   Height          =   4848
   Icon            =   "Form24.frx":0000
   Left            =   864
   LinkTopic       =   "Form24"
   ScaleHeight     =   4524
   ScaleWidth      =   5772
   Top             =   960
   Width           =   5868
   WindowState     =   2  'Maximized
   Begin VB.CommandButton Command1 
      Caption         =   "N"
      BeginProperty Font 
         name            =   "Wingdings"
         charset         =   2
         weight          =   400
         size            =   19.8
         underline       =   0   'False
         italic          =   0   'False
         strikethrough   =   0   'False
      EndProperty
      Height          =   492
      Left            =   4200
      TabIndex        =   9
      Top             =   5640
      Width           =   1092
   End
   Begin VB.Frame Frame1 
      BackColor       =   &H00000000&
      Caption         =   "Microsoft Windows 98"
      ForeColor       =   &H00FFFFFF&
      Height          =   3852
      Left            =   600
      TabIndex        =   4
      Top             =   1680
      Width           =   8532
      Begin VB.Label Label8 
         BackStyle       =   0  'Transparent
         Caption         =   $"Form24.frx":27A2
         ForeColor       =   &H00FFFFFF&
         Height          =   1092
         Left            =   120
         TabIndex        =   8
         Top             =   2760
         Width           =   8172
      End
      Begin VB.Label Label7 
         BackStyle       =   0  'Transparent
         Caption         =   $"Form24.frx":29CC
         ForeColor       =   &H00FFFFFF&
         Height          =   1092
         Left            =   120
         TabIndex        =   7
         Top             =   1680
         Width           =   8292
      End
      Begin VB.Label Label6 
         BackStyle       =   0  'Transparent
         Caption         =   $"Form24.frx":2BB0
         ForeColor       =   &H00FFFFFF&
         Height          =   972
         Left            =   120
         TabIndex        =   6
         Top             =   960
         Width           =   8292
      End
      Begin VB.Label Label5 
         BackStyle       =   0  'Transparent
         Caption         =   $"Form24.frx":2CBD
         ForeColor       =   &H00FFFFFF&
         Height          =   732
         Left            =   120
         TabIndex        =   5
         Top             =   240
         Width           =   8292
      End
   End
   Begin VB.Label Label4 
      Alignment       =   1  'Right Justify
      BackStyle       =   0  'Transparent
      Caption         =   "Microsoft"
      BeginProperty Font 
         name            =   "Times New Roman"
         charset         =   0
         weight          =   700
         size            =   19.8
         underline       =   0   'False
         italic          =   -1  'True
         strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H00FFFFFF&
      Height          =   612
      Left            =   3720
      TabIndex        =   3
      Top             =   720
      Width           =   2052
   End
   Begin VB.Label Label3 
      BackStyle       =   0  'Transparent
      Caption         =   "98"
      BeginProperty Font 
         name            =   "Arial"
         charset         =   0
         weight          =   700
         size            =   48
         underline       =   0   'False
         italic          =   0   'False
         strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H0000FF00&
      Height          =   1092
      Left            =   7800
      TabIndex        =   2
      Top             =   600
      Width           =   1212
   End
   Begin VB.Label Label2 
      Alignment       =   1  'Right Justify
      BackStyle       =   0  'Transparent
      Caption         =   "Windows"
      BeginProperty Font 
         name            =   "Times New Roman"
         charset         =   0
         weight          =   700
         size            =   22.2
         underline       =   0   'False
         italic          =   0   'False
         strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H000000FF&
      Height          =   612
      Left            =   5520
      TabIndex        =   1
      Top             =   720
      Width           =   2172
   End
   Begin VB.Line Line4 
      BorderColor     =   &H00C00000&
      BorderWidth     =   4
      X1              =   480
      X2              =   9240
      Y1              =   6240
      Y2              =   6240
   End
   Begin VB.Label Label1 
      BackStyle       =   0  'Transparent
      Caption         =   "ÿ"
      BeginProperty Font 
         name            =   "Wingdings"
         charset         =   2
         weight          =   400
         size            =   72
         underline       =   0   'False
         italic          =   0   'False
         strikethrough   =   0   'False
      EndProperty
      ForeColor       =   &H0000FFFF&
      Height          =   1332
      Left            =   480
      TabIndex        =   0
      Top             =   120
      Width           =   1812
   End
   Begin VB.Line Line3 
      BorderColor     =   &H00C00000&
      BorderWidth     =   4
      X1              =   9240
      X2              =   9240
      Y1              =   480
      Y2              =   6240
   End
   Begin VB.Line Line2 
      BorderColor     =   &H00FF0000&
      BorderWidth     =   4
      X1              =   480
      X2              =   480
      Y1              =   1440
      Y2              =   6240
   End
   Begin VB.Line Line1 
      BorderColor     =   &H00FF0000&
      BorderWidth     =   4
      X1              =   2160
      X2              =   9240
      Y1              =   480
      Y2              =   480
   End
End
Attribute VB_Name = "Form24"
Attribute VB_Creatable = False
Attribute VB_Exposed = False
Private Sub Command1_Click()
Form25.Show
Form24.Hide
End Sub

Private Sub Form_Load()
Dim cont As Integer
cont = 0
End Sub

Private Sub Timer1_Timer()

End Sub


