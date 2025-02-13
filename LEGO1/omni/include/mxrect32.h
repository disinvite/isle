#ifndef MXRECT32_H
#define MXRECT32_H

#include "mxgeometry.h"
#include "mxpoint32.h"
#include "mxsize32.h"

class MxRect32 : public MxRect<MxS32> {
public:
	// FUNCTION: BETA10 0x1012df70
	MxRect32() {}

	// FUNCTION: BETA10 0x1012de40
	MxRect32(const MxRect32& p_r) : MxRect<MxS32>(p_r) {}

	// FUNCTION: BETA10 0x100d8e90
	MxRect32(MxS32 p_l, MxS32 p_t, MxS32 p_r, MxS32 p_b) : MxRect<MxS32>(p_l, p_t, p_r, p_b) {}

	// FUNCTION: BETA10 0x10137060
	MxRect32(MxPoint32& p_p, MxSize32& p_s) : MxRect<MxS32>(p_p, p_s) {}
};

// TEMPLATE: BETA10 0x100319b0
// MxRect<int>::operator=

// TEMPLATE: BETA10 0x100d8090
// MxRect<int>::GetWidth

// TEMPLATE: BETA10 0x100d80c0
// MxRect<int>::GetHeight

// TEMPLATE: BETA10 0x100ec100
// MxRect<int>::GetLeft

// TEMPLATE: BETA10 0x100ec130
// MxRect<int>::GetTop

// TEMPLATE: BETA10 0x100ec160
// MxRect<int>::GetRight

// TEMPLATE: BETA10 0x100ec190
// MxRect<int>::GetBottom

// TEMPLATE: BETA10 0x100ec1c0
// MxRect<int>::operator+=

// TEMPLATE: BETA10 0x1012dec0
// MxRect<int>::operator&=

// SYNTHETIC: LEGO1 0x100b6fc0
// SYNTHETIC: BETA10 0x1012dfa0
// MxRect32::operator=

// TEMPLATE: BETA10 0x10031d30
// MxRect<int>::Contains

// TEMPLATE: BETA10 0x10137090
// MxRect<int>::Intersects

// TEMPLATE: BETA10 0x10137100
// MxRect<int>::operator-=

// TEMPLATE: BETA10 0x1014b320
// MxRect<int>::operator|=

// TEMPLATE: BETA10 0x1014b2d0
// MxRect<int>::Empty

// TEMPLATE: BETA10 0x1014bd80
// MxRect<int>::SetLeft

// TEMPLATE: BETA10 0x1014b270
// MxRect<int>::SetTop

// TEMPLATE: BETA10 0x1014bda0
// MxRect<int>::SetRight

// TEMPLATE: BETA10 0x1014b2a0
// MxRect<int>::SetBottom

#endif // MXRECT32_H
