#include "legobackgroundcolor.h"

#include "3dmanager/lego3dmanager.h"
#include "decomp.h"
#include "legoutils.h"
#include "legovideomanager.h"
#include "misc.h"

#include <stdio.h>

DECOMP_SIZE_ASSERT(LegoBackgroundColor, 0x30)

// GLOBAL: LEGO1 0x100f3fb0
// STRING: LEGO1 0x100f3a18
// GLOBAL: BETA10 0x101ed738
// STRING: BETA10 0x101edb84
const char* g_delimiter = " \t";

// GLOBAL: LEGO1 0x100f3fb4
// STRING: LEGO1 0x100f3bf0
// GLOBAL: BETA10 0x101ed73c
// STRING: BETA10 0x101edb88
const char* g_set = "set";

// GLOBAL: LEGO1 0x100f3fb8
// STRING: LEGO1 0x100f0cdc
// GLOBAL: BETA10 0x101ed740
// STRING: BETA10 0x101edb8c
const char* g_reset = "reset";

// FUNCTION: LEGO1 0x1003bfb0
LegoBackgroundColor::LegoBackgroundColor(const char* p_key, const char* p_value)
{
	m_key = p_key;
	m_key.ToUpperCase();
	SetValue(p_value);
}

// FUNCTION: LEGO1 0x1003c070
// FUNCTION: BETA10 0x10086634
void LegoBackgroundColor::SetValue(const char* p_colorString)
{
	m_value = p_colorString;
	m_value.ToLowerCase();

	LegoVideoManager* videomanager = VideoManager();
	if (videomanager && p_colorString) {
		float convertedR, convertedG, convertedB;
		// DECOMP: Beta calls m_value.GetData(). Is the string copy an inline
		// function of MxString?
		char* colorStringCopy = strcpy(new char[strlen(p_colorString) + 1], p_colorString);
		char* colorStringSplit = strtok(colorStringCopy, g_delimiter);

		if (!strcmp(colorStringSplit, g_set)) {
			colorStringSplit = strtok(NULL, g_delimiter);
			if (colorStringSplit) {
				m_h = (float) (atoi(colorStringSplit) / 100.0);
			}

			colorStringSplit = strtok(NULL, g_delimiter);
			if (colorStringSplit) {
				m_s = (float) (atoi(colorStringSplit) / 100.0);
			}

			colorStringSplit = strtok(NULL, g_delimiter);
			if (colorStringSplit) {
				m_v = (float) (atoi(colorStringSplit) / 100.0);
			}

			ConvertHSVToRGB(m_h, m_s, m_v, &convertedR, &convertedG, &convertedB);
			videomanager->SetSkyColor(convertedR, convertedG, convertedB);
		}
		else if (!strcmp(colorStringSplit, g_reset)) {
			ConvertHSVToRGB(m_h, m_s, m_v, &convertedR, &convertedG, &convertedB);
			videomanager->SetSkyColor(convertedR, convertedG, convertedB);
		}

		delete[] colorStringCopy;
	}
}

// FUNCTION: LEGO1 0x1003c230
// FUNCTION: BETA10 0x100867f9
void LegoBackgroundColor::ToggleDayNight(MxBool p_sun)
{
	char buffer[30];

	if (p_sun) {
		m_s += 0.1;
		if (m_s > 0.9) {
			m_s = 1.0;
		}
	}
	else {
		m_s -= 0.1;
		if (m_s < 0.1) {
			m_s = 0.1;
		}
	}

	sprintf(buffer, "set %d %d %d", (MxU32) (m_h * 100.0f), (MxU32) (m_s * 100.0f), (MxU32) (m_v * 100.0f));
	m_value = buffer;

	float convertedR, convertedG, convertedB;
	ConvertHSVToRGB(m_h, m_s, m_v, &convertedR, &convertedG, &convertedB);
	VideoManager()->SetSkyColor(convertedR, convertedG, convertedB);
	SetLightColor(convertedR, convertedG, convertedB);
}

// FUNCTION: LEGO1 0x1003c330
// FUNCTION: BETA10 0x100868de
void LegoBackgroundColor::ToggleSkyColor()
{
	char buffer[30];

	m_h += 0.05;
	if (m_h > 1.0) {
		m_h -= 1.0;
	}

	sprintf(buffer, "set %d %d %d", (MxU32) (m_h * 100.0f), (MxU32) (m_s * 100.0f), (MxU32) (m_v * 100.0f));
	m_value = buffer;

	float convertedR, convertedG, convertedB;
	ConvertHSVToRGB(m_h, m_s, m_v, &convertedR, &convertedG, &convertedB);
	VideoManager()->SetSkyColor(convertedR, convertedG, convertedB);
	SetLightColor(convertedR, convertedG, convertedB);
}

// FUNCTION: LEGO1 0x1003c400
// FUNCTION: BETA10 0x10086984
void LegoBackgroundColor::SetLightColor(float p_r, float p_g, float p_b)
{
	if (!VideoManager()->GetVideoParam().Flags().GetF2bit0()) {
		// TODO: Computed constants based on what?
		p_r /= 0.23;
		p_g /= 0.63;
		p_b /= 0.85;

		if (p_r > 1.0) {
			p_r = 1.0;
		}

		if (p_g > 1.0) {
			p_g = 1.0;
		}

		if (p_b > 1.0) {
			p_b = 1.0;
		}

		VideoManager()->Get3DManager()->GetLego3DView()->SetLightColor(FALSE, p_r, p_g, p_b);
		VideoManager()->Get3DManager()->GetLego3DView()->SetLightColor(TRUE, p_r, p_g, p_b);
	}
}

// FUNCTION: LEGO1 0x1003c4b0
void LegoBackgroundColor::SetLightColor()
{
	float convertedR, convertedG, convertedB;
	ConvertHSVToRGB(m_h, m_s, m_v, &convertedR, &convertedG, &convertedB);
	SetLightColor(convertedR, convertedG, convertedB);
}
