#ifndef MXRECT16_H
#define MXRECT16_H

#include "mxgeometry.h"
#include "mxtypes.h"

class MxPoint16 : public MxPoint<MxS16> {
public:
	MxPoint16() {}
	MxPoint16(const MxPoint16& p_p) : MxPoint<MxS16>(p_p) {}
	MxPoint16(MxS16 p_x, MxS16 p_y) : MxPoint<MxS16>(p_x, p_y) {}
};

class MxSize16 : public MxSize<MxS16> {
public:
	MxSize16() {}
	MxSize16(const MxSize16& p_s) : MxSize<MxS16>(p_s) {}
	MxSize16(MxS16 p_width, MxS16 p_height) : MxSize<MxS16>(p_width, p_height) {}
};

class MxRect16 : public MxRect<MxS16> {
public:
	// FUNCTION: BETA10 0x10097eb0
	MxRect16() {}
	MxRect16(const MxRect16& p_r) : MxRect<MxS16>(p_r) {}
	MxRect16(MxS16 p_l, MxS16 p_t, MxS16 p_r, MxS16 p_b) : MxRect<MxS16>(p_l, p_t, p_r, p_b) {}
	MxRect16(MxPoint16& p_p, MxSize16& p_s) : MxRect<MxS16>(p_p, p_s) {}
};

// TEMPLATE: BETA10 0x10097ee0
// MxRect<short>::MxRect<short>
// todo

// TEMPLATE: BETA10 0x100981f0
// MxRect<short>::SetLeft

// TEMPLATE: BETA10 0x10098220
// MxRect<short>::SetTop

// TEMPLATE: BETA10 0x10098250
// MxRect<short>::SetRight

// TEMPLATE: BETA10 0x10098280
// MxRect<short>::SetBottom

// TEMPLATE: BETA10 0x10098300
// MxRect<short>::GetLeft

// TEMPLATE: BETA10 0x10098330
// MxRect<short>::GetTop

// TEMPLATE: BETA10 0x10098360
// MxRect<short>::GetBottom

// TEMPLATE: BETA10 0x10098390
// MxRect<short>::GetWidth

// TEMPLATE: BETA10 0x100983c0
// MxRect<short>::GetHeight

#endif // MXRECT16_H
