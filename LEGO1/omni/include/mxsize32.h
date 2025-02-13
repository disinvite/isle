#ifndef MXSIZE32_H
#define MXSIZE32_H

#include "mxgeometry.h"
#include "mxtypes.h"

class MxSize32 : public MxSize<MxS32> {
public:
	MxSize32() {}
	MxSize32(const MxSize32& p_s) : MxSize<MxS32>(p_s) {}

	// FUNCTION: BETA10 0x10137030
	MxSize32(MxS32 p_width, MxS32 p_height) : MxSize<MxS32>(p_width, p_height) {}
};

// TEMPLATE: BETA10 0x10031820
// ??0?$MxSize@H@@QAE@HH@Z

// TEMPLATE: BETA10 0x10031950
// MxSize<int>::GetWidth

// TEMPLATE: BETA10 0x10031980
// MxSize<int>::GetHeight

#endif // MXSIZE32_H
