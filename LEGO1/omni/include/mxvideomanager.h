#ifndef MXVIDEOMANAGER_H
#define MXVIDEOMANAGER_H

#include "mxpresentationmanager.h"
#include "mxvideoparam.h"

#include <d3d.h>

class MxDisplaySurface;
class MxRect32;
class MxRegion;

// VTABLE: LEGO1 0x100dc810
// VTABLE: BETA10 0x101c1bf8
// SIZE 0x64
class MxVideoManager : public MxPresentationManager {
public:
	MxVideoManager();
	~MxVideoManager() override;

	MxResult Tickle() override; // vtable+0x08
	void Destroy() override;    // vtable+0x18
	virtual MxResult VTable0x28(
		MxVideoParam& p_videoParam,
		LPDIRECTDRAW p_pDirectDraw,
		LPDIRECT3D2 p_pDirect3D,
		LPDIRECTDRAWSURFACE p_ddSurface1,
		LPDIRECTDRAWSURFACE p_ddSurface2,
		LPDIRECTDRAWCLIPPER p_ddClipper,
		MxU32 p_frequencyMS,
		MxBool p_createThread
	);                                                                                               // vtable+0x28
	virtual MxResult Create(MxVideoParam& p_videoParam, MxU32 p_frequencyMS, MxBool p_createThread); // vtable+0x2c
	virtual MxResult RealizePalette(MxPalette* p_palette);                                           // vtable+0x30
	virtual void UpdateView(MxU32 p_x, MxU32 p_y, MxU32 p_width, MxU32 p_height);                    // vtable+0x34

	MxResult Init();
	void Destroy(MxBool p_fromDestructor);
	void InvalidateRect(MxRect32& p_rect);
	void SortPresenterList();
	void UpdateRegion();

	MxVideoParam& GetVideoParam() { return this->m_videoParam; }
	LPDIRECTDRAW GetDirectDraw() { return this->m_pDirectDraw; }

	// FUNCTION: BETA10 0x1002e290
	MxDisplaySurface* GetDisplaySurface() { return this->m_displaySurface; }

	MxRegion* GetRegion() { return this->m_region; }

	// SYNTHETIC: LEGO1 0x100be280
	// SYNTHETIC: BETA10 0x1012de00
	// MxVideoManager::`scalar deleting destructor'

protected:
	MxVideoParam m_videoParam;          // 0x2c
	LPDIRECTDRAW m_pDirectDraw;         // 0x50
	LPDIRECT3D2 m_pDirect3D;            // 0x54
	MxDisplaySurface* m_displaySurface; // 0x58
	MxRegion* m_region;                 // 0x5c
	MxBool m_unk0x60;                   // 0x60
};

#endif // MXVIDEOMANAGER_H
