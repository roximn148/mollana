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

var
  DeleteUserData: Boolean;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  dataDir: String;
  form: TForm;
  captionLabel: TLabel;
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
      form := TForm.Create(nil);
      form.Caption := 'Uninstall Mollana';
      form.BorderStyle := bsDialog;
      form.Position := poScreenCenter;
      form.Width := 400;
      form.Height := 140;

      captionLabel := TLabel.Create(form);
      captionLabel.Parent := form;
      captionLabel.Left := 12;
      captionLabel.Top := 12;
      captionLabel.Width := 370;
      captionLabel.WordWrap := True;
      captionLabel.Caption := 'Remove Mollana''s user data (preferences, dictionaries, and logs)?';

      checkBox := TCheckBox.Create(form);
      checkBox.Parent := form;
      checkBox.Left := 12;
      checkBox.Top := 52;
      checkBox.Caption := 'Remove user data';

      okButton := TButton.Create(form);
      okButton.Parent := form;
      okButton.Left := 170;
      okButton.Top := 84;
      okButton.Width := 75;
      okButton.Caption := 'OK';
      okButton.ModalResult := mrOK;
      okButton.Default := True;

      cancelButton := TButton.Create(form);
      cancelButton.Parent := form;
      cancelButton.Left := 258;
      cancelButton.Top := 84;
      cancelButton.Width := 75;
      cancelButton.Caption := 'Cancel';
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
