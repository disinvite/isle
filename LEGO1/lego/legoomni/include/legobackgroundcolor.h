#ifndef LEGOBACKGROUNDCOLOR_H
#define LEGOBACKGROUNDCOLOR_H

#include "mxvariable.h"

// VTABLE: LEGO1 0x100d74a8
// VTABLE: BETA10 0x101bc4f0
// SIZE 0x30
class LegoBackgroundColor : public MxVariable {
public:
	LegoBackgroundColor(const char* p_key, const char* p_value);

	void SetValue(const char* p_colorString) override;
	void SetLightColor(float p_r, float p_g, float p_b);
	void SetLightColor();
	void ToggleDayNight(MxBool);
	void ToggleSkyColor();

private:
	float m_h;
	float m_s;
	float m_v;
};

#endif // LEGOBACKGROUNDCOLOR_H
