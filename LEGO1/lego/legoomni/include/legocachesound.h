#ifndef LEGOCACHESOUND_H
#define LEGOCACHESOUND_H

#include "decomp.h"
#include "legounknown100d5778.h"
#include "mxcore.h"
#include "mxstring.h"

// VTABLE: LEGO1 0x100d4718
// SIZE 0x88
class LegoCacheSound : public MxCore {
public:
	LegoCacheSound();
	~LegoCacheSound() override; // vtable+0x00

	// FUNCTION: LEGO1 0x10006580
	inline const char* ClassName() const override // vtable+0x0c
	{
		// STRING: LEGO1 0x100f01c4
		return "LegoCacheSound";
	}

	// FUNCTION: LEGO1 0x10006590
	inline MxBool IsA(const char* p_name) const override // vtable+0x10
	{
		return !strcmp(p_name, LegoCacheSound::ClassName()) || MxCore::IsA(p_name);
	}

	inline const MxString& GetString0x48() const { return m_string0x48; }
	inline const undefined GetUnk0x58() { return m_unk0x58; }

	void FUN_10006b80();
	void FUN_10006be0();

	// SYNTHETIC: LEGO1 0x10006610
	// LegoCacheSound::`scalar deleting destructor'

private:
	void Init();

	undefined4 m_unk0x8;           // 0x08
	undefined m_unk0xc[4];         // 0x0c
	LegoUnknown100d5778 m_unk0x10; // 0x10
	undefined4 m_unk0x40;          // 0x40
	undefined m_unk0x44[4];        // 0x44
	MxString m_string0x48;         // 0x48
	undefined m_unk0x58;           // 0x58
	undefined m_unk0x59[0x10];     // 0x59
	undefined m_unk0x69;           // 0x69
	undefined m_unk0x6a;           // 0x6a
	undefined4 m_unk0x6c;          // 0x6c
	undefined m_unk0x70;           // 0x70
	MxString m_string0x74;         // 0x74
	undefined m_unk0x84;           // 0x84
};

#endif // LEGOCACHESOUND_H
