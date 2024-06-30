#if !defined(AFX_CONFIGCOMMANDLINEINFO_H)
#define AFX_CONFIGCOMMANDLINEINFO_H

#include "StdAfx.h"
#include "compat.h"
#include "config.h"
#include "decomp.h"

// VTABLE: CONFIG 0x4060e8
// SIZE 0x24
class CConfigCommandLineInfo : public CCommandLineInfo {
public:
	CConfigCommandLineInfo();
	// FUNCTION: CONFIG 0x403ba0
	virtual ~CConfigCommandLineInfo() {}

	void ParseParam(LPCSTR pszParam, BOOL bFlag, BOOL bLast) override;
};

// SYNTHETIC: CONFIG 0x403b80
// CConfigCommandLineInfo::`scalar deleting destructor'

#endif // !defined(AFX_CONFIGCOMMANDLINEINFO_H)
