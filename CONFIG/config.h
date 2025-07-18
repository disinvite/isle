#if !defined(AFX_CONFIG_H)
#define AFX_CONFIG_H

#include "StdAfx.h"
#include "compat.h"
#include "decomp.h"

#include <d3d.h>

class LegoDeviceEnumerate;
struct Direct3DDeviceInfo;
struct MxDriver;

#define currentConfigApp ((CConfigApp*) AfxGetApp())

// VTABLE: CONFIG 0x00406040
// VTABLE: CONFIGD 0x0040c0a0
// SIZE 0x108
class CConfigApp : public CWinApp {
public:
	CConfigApp();

	// Overrides
	// ClassWizard generated virtual function overrides
	//{{AFX_VIRTUAL(CConfigApp)

public:
	BOOL InitInstance() override;
	int ExitInstance() override;
	//}}AFX_VIRTUAL

	// Implementation

	BOOL WriteReg(const char* p_key, const char* p_value) const;
	BOOL ReadReg(LPCSTR p_key, LPCSTR p_value, DWORD p_size) const;
	BOOL ReadRegBool(LPCSTR p_key, BOOL* p_bool) const;
	BOOL ReadRegInt(LPCSTR p_key, int* p_value) const;
	BOOL IsDeviceInBasicRGBMode() const;
	D3DCOLORMODEL GetHardwareDeviceColorModel() const;
	BOOL IsPrimaryDriver() const;
	BOOL ReadRegisterSettings();
	BOOL ValidateSettings();
	DWORD GetConditionalDeviceRenderBitDepth() const;
	DWORD GetDeviceRenderBitStatus() const;
	BOOL AdjustDisplayBitDepthBasedOnRenderStatus();
	void WriteRegisterSettings() const;

	//{{AFX_MSG(CConfigApp)
	// NOTE - the ClassWizard will add and remove member functions here.
	//    DO NOT EDIT what you see in these blocks of generated code !
	//}}AFX_MSG
	DECLARE_MESSAGE_MAP()

private:
	BOOL IsLegoNotRunning();

public:
	LegoDeviceEnumerate* m_dxInfo; // 0x0c4
	MxDriver* m_ddInfo;            // 0x0c8
	Direct3DDeviceInfo* m_d3dInfo; // 0x0cc
	int m_display_bit_depth;       // 0x0d0
	BOOL m_flip_surfaces;          // 0x0d4
	BOOL m_full_screen;            // 0x0d8
	BOOL m_3d_video_ram;           // 0x0dc
	BOOL m_wide_view_angle;        // 0x0e0
	BOOL m_3d_sound;               // 0x0e4
	BOOL m_draw_cursor;            // 0x0e8
	BOOL m_use_joystick;           // 0x0ec
	int m_joystick_index;          // 0x0f0
	BOOL m_run_config_dialog;      // 0x0f4
	int m_model_quality;           // 0x0f8
	int m_texture_quality;         // 0x0fc
	undefined m_unk0x100[4];       // 0x100
	BOOL m_music;                  // 0x104
};

// SYNTHETIC: CONFIG 0x00402cd0
// SYNTHETIC: CONFIGD 0x00408330
// CConfigApp::`scalar deleting destructor'

// FUNCTION: CONFIG 0x402c20
// FUNCTION: CONFIGD 0x4068d0
// CConfigApp::_GetBaseMessageMap

// FUNCTION: CONFIG 0x402c30
// FUNCTION: CONFIGD 0x4068e5
// CConfigApp::GetMessageMap

// GLOBAL: CONFIG 0x406008
// GLOBAL: CONFIGD 0x40c058
// CConfigApp::messageMap

// GLOBAL: CONFIG 0x406010
// GLOBAL: CONFIGD 0x40c060
// CConfigApp::_messageEntries

#endif // !defined(AFX_CONFIG_H)
