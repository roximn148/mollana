; Mollana Windows installer, built with Inno Setup 6.
;
; Build the application first:
;   uv run python scripts/compileUI.py
;   uv run pyinstaller --clean --noconfirm mollana.spec
;
; PyInstaller writes build\version.iss from pyproject.toml, so this script must
; be compiled after the application build. Either open this file in the Inno
; Setup IDE after building, or run:
;   scripts\generate-win-setup.bat

#include "..\build\version.iss"

#define AppName "Mollana"
#define AppPublisher "RoXimn"
#define AppURL "https://github.com/roximn148/mollana"
#define AppExeName "Mollana.exe"

[Setup]
AppId={{1a0a9f40-4a60-5cdf-8866-e3aa024860a6}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
AppUpdatesURL={#AppURL}/releases
VersionInfoVersion={#AppVersionNumeric}
VersionInfoCompany={#AppPublisher}
VersionInfoDescription={#AppName} Setup
VersionInfoProductName={#AppName}
VersionInfoProductVersion={#AppVersionNumeric}
DefaultDirName={localappdata}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE.txt
OutputDir=..\dist
OutputBaseFilename={#AppName}-{#AppVersion}-win64-setup
SetupIconFile=..\src\mollana\ui\resources\images\mollana.ico
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName} {#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\Mollana\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autoprograms}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[Code]
// The user data directory ({localappdata}\mollana: preferences, dictionaries,
// and logs) is kept by uninstallation by default. When the user starts an
// interactive uninstall, the script below offers to remove it, with an opt-in
// checkbox: unchecked, the data is kept; checked, it is removed after the
// uninstaller has finished deleting the application files. Silent uninstalls
// (/SILENT, /VERYSILENT) never see the dialog.
//
// Layout notes: the dialog is built with CreateCustomForm so it inherits Inno's
// DPI-aware dialog font, and every coordinate goes through ScaleX/ScaleY.
// TLabel.AutoSize defaults to True, which discards an explicit Width and
// collapses WordWrap text into a narrow column, so it must be turned off before
// the bounds are set.

var
  DeleteUserData: Boolean;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  dataDir: String;
  form: TSetupForm;
  questionLabel: TLabel;
  warningLabel: TLabel;
  checkBox: TCheckBox;
  okButton: TButton;
  cancelButton: TButton;
  formResult: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    DeleteUserData := False;
    dataDir := ExpandConstant('{localappdata}\mollana');
    if (not UninstallSilent()) and DirExists(dataDir) then
    begin
      form := CreateCustomForm(ScaleX(420), ScaleY(176), True, True);
      form.Caption := 'Uninstall Mollana';
      form.Position := poScreenCenter;

      questionLabel := TLabel.Create(form);
      questionLabel.Parent := form;
      questionLabel.WordWrap := True;
      questionLabel.Caption :=
        'Remove Mollana''s user data (preferences, dictionaries, and logs)?';
      questionLabel.AutoSize := False;
      questionLabel.Left := ScaleX(16);
      questionLabel.Top := ScaleY(12);
      questionLabel.Width := ScaleX(388);
      questionLabel.Height := ScaleY(30);

      warningLabel := TLabel.Create(form);
      warningLabel.Parent := form;
      warningLabel.WordWrap := True;
      warningLabel.Caption :=
        'Warning: checking this box permanently deletes every saved dictionary ' +
        'in that folder. Back up your dictionaries first if you want to keep them.';
      warningLabel.AutoSize := False;
      warningLabel.Left := ScaleX(16);
      warningLabel.Top := ScaleY(46);
      warningLabel.Width := ScaleX(388);
      warningLabel.Height := ScaleY(48);

      checkBox := TCheckBox.Create(form);
      checkBox.Parent := form;
      checkBox.Caption := 'Remove user data';
      checkBox.Left := ScaleX(16);
      checkBox.Top := ScaleY(100);
      checkBox.Width := ScaleX(388);

      okButton := TButton.Create(form);
      okButton.Parent := form;
      okButton.Caption := 'OK';
      okButton.Left := ScaleX(240);
      okButton.Top := ScaleY(136);
      okButton.Width := ScaleX(78);
      okButton.Height := ScaleY(25);
      okButton.ModalResult := mrOK;
      okButton.Default := True;

      cancelButton := TButton.Create(form);
      cancelButton.Parent := form;
      cancelButton.Caption := 'Cancel';
      cancelButton.Left := ScaleX(326);
      cancelButton.Top := ScaleY(136);
      cancelButton.Width := ScaleX(78);
      cancelButton.Height := ScaleY(25);
      cancelButton.ModalResult := mrCancel;
      cancelButton.Cancel := True;

      formResult := form.ShowModal;
      if (formResult = mrOK) and checkBox.Checked then
        DeleteUserData := True;
      form.Free;
    end;
  end
  else if (CurUninstallStep = usPostUninstall) and DeleteUserData then
  begin
    DelTree(ExpandConstant('{localappdata}\mollana'), True, True, True);
  end;
end;
