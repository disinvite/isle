#ifndef LEGOUNKNOWN100D5778_H
#define LEGOUNKNOWN100D5778_H

#include "decomp.h"
#include "mxtypes.h"
#include "roi/legoroi.h"

#include <dsound.h>

// VTABLE: LEGO1 0x100d5778
// SIZE 0x30
class LegoUnknown100d5778 {
public:
	LegoUnknown100d5778();
	virtual ~LegoUnknown100d5778();
	void Init();
	void FUN_10011880();

	// SYNTHETIC: LEGO1 0x10011650
	// LegoUnknown100d5778::`scalar deleting destructor'

private:
	undefined m_unk0x4[4];     // 0x04
	LPDIRECTSOUND m_unk0x8;    // 0x08 (TODO: Not certain of type)
	LegoROI* m_unk0xc;         // 0x0c
	undefined4 m_unk0x10;      // 0x10
	MxBool m_unk0x14;          // 0x14
	MxBool m_unk0x15;          // 0x15
	undefined4 m_unk0x18;      // 0x18
	undefined m_unk0x1c[0x10]; // 0x1c
	undefined4 m_unk0x2c;      // 0x2c
};

#endif // LEGOUNKNOWN100D5778_H
