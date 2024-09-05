#include "mxdssource.h"

#include "mxdsbuffer.h"

DECOMP_SIZE_ASSERT(MxDSSource, 0x14)

// FUNCTION: LEGO1 0x100bff60
// FUNCTION: BETA10 0x10148b70
MxDSSource::~MxDSSource()
{
	delete[] m_pBuffer;
}

// FUNCTION: LEGO1 0x100bffd0
MxResult MxDSSource::ReadToBuffer(MxDSBuffer* p_buffer)
{
	return Read(p_buffer->GetBuffer(), p_buffer->GetWriteOffset());
}

// FUNCTION: LEGO1 0x100bfff0
MxLong MxDSSource::GetLengthInDWords()
{
	return m_lengthInDWords;
}

// FUNCTION: LEGO1 0x100c0000
MxU32* MxDSSource::GetBuffer()
{
	return m_pBuffer;
}

// FUNCTION: LEGO1 0x100c0010
// FUNCTION: BETA10 0x10148cc0
const char* MxDSSource::ClassName() const
{
	// STRING: LEGO1 0x10102588
	return "MxDSSource";
}

// FUNCTION: LEGO1 0x100c0020
// FUNCTION: BETA10 0x10148ce0
MxBool MxDSSource::IsA(const char* p_name) const
{
	return !strcmp(p_name, MxDSSource::ClassName()) || MxCore::IsA(p_name);
}
