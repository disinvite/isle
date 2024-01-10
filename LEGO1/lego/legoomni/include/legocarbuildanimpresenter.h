#ifndef LEGOCARBUILDANIMPRESENTER_H
#define LEGOCARBUILDANIMPRESENTER_H

#include "legoanimpresenter.h"

// VTABLE: LEGO1 0x100d99e0
// SIZE 0x150
class LegoCarBuildAnimPresenter : public LegoAnimPresenter {
public:
	LegoCarBuildAnimPresenter();
	virtual ~LegoCarBuildAnimPresenter() override; // vtable+0x0

	// FUNCTION: LEGO1 0x10078510
	inline virtual const char* ClassName() const override // vtable+0x0c
	{
		// STRING: LEGO1 0x100f05ec
		return "LegoCarBuildAnimPresenter";
	}

	// FUNCTION: LEGO1 0x10078520
	inline virtual MxBool IsA(const char* p_name) const override // vtable+0x10
	{
		return !strcmp(p_name, LegoCarBuildAnimPresenter::ClassName()) || LegoAnimPresenter::IsA(p_name);
	}
};

#endif // LEGOCARBUILDANIMPRESENTER_H