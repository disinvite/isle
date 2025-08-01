#ifndef MXSMKPRESENTER_H
#define MXSMKPRESENTER_H

#include "decomp.h"
#include "mxsmk.h"
#include "mxvideopresenter.h"

// VTABLE: LEGO1 0x100dc348
// SIZE 0x720
class MxSmkPresenter : public MxVideoPresenter {
public:
	MxSmkPresenter();
	~MxSmkPresenter() override;

	// FUNCTION: BETA10 0x1012f010
	static const char* HandlerClassName()
	{
		// STRING: LEGO1 0x10101e38
		return "MxSmkPresenter";
	}

	// FUNCTION: LEGO1 0x100b3730
	// FUNCTION: BETA10 0x1013b8c0
	const char* ClassName() const override // vtable+0x0c
	{
		return HandlerClassName();
	}

	// FUNCTION: LEGO1 0x100b3740
	MxBool IsA(const char* p_name) const override // vtable+0x10
	{
		return !strcmp(p_name, MxSmkPresenter::ClassName()) || MxVideoPresenter::IsA(p_name);
	}

	MxResult AddToManager() override;                 // vtable+0x34
	void Destroy() override;                          // vtable+0x38
	void LoadHeader(MxStreamChunk* p_chunk) override; // vtable+0x5c
	void CreateBitmap() override;                     // vtable+0x60
	void LoadFrame(MxStreamChunk* p_chunk) override;  // vtable+0x68
	void RealizePalette() override;                   // vtable+0x70
	virtual void ResetCurrentFrameAtEnd();            // vtable+0x88

	// SYNTHETIC: LEGO1 0x100b3850
	// MxSmkPresenter::`scalar deleting destructor'

private:
	void Init();
	void Destroy(MxBool p_fromDestructor);

protected:
	MxSmk m_mxSmk;        // 0x64
	MxU32 m_currentFrame; // 0x71c
};

#endif // MXSMKPRESENTER_H
