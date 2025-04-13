#include "viewmanager.h"

#include "mxdirectx/mxstopwatch.h"
#include "tgl/d3drm/impl.h"
#include "viewlod.h"

#include <vec.h>

DECOMP_SIZE_ASSERT(ViewManager, 0x1bc)

// GLOBAL: LEGO1 0x100dbc78
int g_boundingBoxCornerMap[8][3] =
	{{0, 0, 0}, {0, 0, 1}, {0, 1, 0}, {1, 0, 0}, {0, 1, 1}, {1, 0, 1}, {1, 1, 0}, {1, 1, 1}};

// GLOBAL: LEGO1 0x100dbcd8
// GLOBAL: BETA10 0x101c33f8
int g_planePointIndexMap[18] = {0, 1, 5, 6, 2, 3, 3, 0, 4, 1, 2, 6, 0, 3, 2, 4, 5, 6};

// GLOBAL: LEGO1 0x10101050
// GLOBAL: BETA10 0x10205914
float g_LODScaleFactor = 4.0F;

// GLOBAL: LEGO1 0x10101054
// GLOBAL: BETA10 0x10205918
float g_minLODThreshold = 0.00097656297;

// GLOBAL: LEGO1 0x10101058
// GLOBAL: BETA10 0x1020591c
int g_maxLODLevels = 6;

// GLOBAL: LEGO1 0x1010105c
// GLOBAL: BETA10 0x1020592c
float g_unk0x1010105c = 0.000125F;

// GLOBAL: LEGO1 0x10101060
float g_elapsedSeconds = 0;

inline void SetAppData(ViewROI* p_roi, LPD3DRM_APPDATA data);
inline BOOL GetD3DRM(IDirect3DRM2*& p_d3drm, Tgl::Renderer* p_tglRenderer);
inline BOOL GetFrame(IDirect3DRMFrame2*& frame, Tgl::Group* scene);

// FUNCTION: LEGO1 0x100a5eb0
// FUNCTION: BETA10 0x10171cb3
ViewManager::ViewManager(Tgl::Renderer* pRenderer, Tgl::Group* scene, const OrientableROI* point_of_view)
	: scene(scene), flags(c_bit1 | c_bit2 | c_bit3 | c_bit4)
{
	SetPOVSource(point_of_view);
	prev_render_time = 0.09;
	GetD3DRM(d3drm, pRenderer);
	GetFrame(frame, scene);
	width = 0.0;
	height = 0.0;
	view_angle = 0.0;
	pov.SetIdentity();
	front = 0.0;
	back = 0.0;

	memset(transformed_points, 0, sizeof(transformed_points));
	seconds_allowed = 1.0;
}

// FUNCTION: LEGO1 0x100a60c0
ViewManager::~ViewManager()
{
	SetPOVSource(NULL);
}

// FUNCTION: LEGO1 0x100a6150
// FUNCTION: BETA10 0x10172164
unsigned int ViewManager::IsBoundingBoxInFrustum(const BoundingBox& p_bounding_box)
{
	const Vector3* box[] = {&p_bounding_box.Min(), &p_bounding_box.Max()};

	float und[8][3];
	int i, j, k;

	for (i = 0; i < 8; i++) {
		for (j = 0; j < 3; j++) {
			und[i][j] = box[g_boundingBoxCornerMap[i][j]]->operator[](j);
		}
	}

	for (i = 0; i < 6; i++) {
		for (k = 0; k < 8; k++) {
			if (frustum_planes[i][0] * und[k][0] + frustum_planes[i][2] * und[k][2] + frustum_planes[i][1] * und[k][1] +
					frustum_planes[i][3] >=
				0.0f) {
				break;
			}
		}

		if (k == 8) {
			return FALSE;
		}
	}

	return TRUE;
}

// FUNCTION: LEGO1 0x100a6410
// FUNCTION: BETA10 0x101722cd
void ViewManager::Remove(ViewROI* p_roi)
{
	for (CompoundObject::iterator it = rois.begin(); it != rois.end(); it++) {
		if (*it == p_roi) {
			rois.erase(it);

			if (p_roi->GetUnknown0xe0() >= 0) {
				RemoveROIDetailFromScene(p_roi);
			}

			const CompoundObject* comp = p_roi->GetComp();

			if (comp != NULL) {
				for (CompoundObject::const_iterator it = comp->begin(); it != comp->end(); ++it) {
					if (((ViewROI*) *it)->GetUnknown0xe0() >= 0) {
						RemoveROIDetailFromScene((ViewROI*) *it);
					}
				}
			}

			return;
		}
	}
}

// FUNCTION: LEGO1 0x100a64d0
// FUNCTION: BETA10 0x101723f5
void ViewManager::RemoveAll(ViewROI* p_roi)
{
	if (p_roi == NULL) {
		for (CompoundObject::iterator it = rois.begin(); it != rois.end(); it++) {
			RemoveAll((ViewROI*) *it);
		}

		rois.erase(rois.begin(), rois.end());
	}
	else {
		if (p_roi->GetUnknown0xe0() >= 0) {
			RemoveROIDetailFromScene(p_roi);
		}

		p_roi->SetUnknown0xe0(-1);
		const CompoundObject* comp = p_roi->GetComp();

		if (comp != NULL) {
			for (CompoundObject::const_iterator it = comp->begin(); it != comp->end(); ++it) {
				if ((ViewROI*) *it != NULL) {
					RemoveAll((ViewROI*) *it);
				}
			}
		}
	}
}

// FUNCTION: LEGO1 0x100a65b0
// FUNCTION: BETA10 0x1017254b
void ViewManager::UpdateROIDetailBasedOnLOD(ViewROI* p_roi, int p_und)
{
	if (p_roi->GetLODCount() <= p_und) {
		p_und = p_roi->GetLODCount() - 1;
	}

	int unk0xe0 = p_roi->GetUnknown0xe0();

	if (unk0xe0 == p_und) {
		return;
	}

	Tgl::Group* group = p_roi->GetGeometry();
	Tgl::MeshBuilder* meshBuilder;
	ViewLOD* lod;

	if (unk0xe0 < 0) {
		lod = (ViewLOD*) p_roi->GetLOD(p_und);

		if (lod->GetUnknown0x08() & ViewLOD::c_bit4) {
			scene->Add((Tgl::MeshBuilder*) group);
			SetAppData(p_roi, reinterpret_cast<LPD3DRM_APPDATA>(p_roi));
		}
	}
	else {
		lod = (ViewLOD*) p_roi->GetLOD(unk0xe0);

		if (lod != NULL) {
			meshBuilder = lod->GetMeshBuilder();

			if (meshBuilder != NULL) {
				group->Remove(meshBuilder);
			}
		}

		lod = (ViewLOD*) p_roi->GetLOD(p_und);
	}

	if (lod->GetUnknown0x08() & ViewLOD::c_bit4) {
		meshBuilder = lod->GetMeshBuilder();

		if (meshBuilder != NULL) {
			group->Add(meshBuilder);
			SetAppData(p_roi, reinterpret_cast<LPD3DRM_APPDATA>(p_roi));
			p_roi->SetUnknown0xe0(p_und);
			return;
		}
	}

	p_roi->SetUnknown0xe0(-1);
}

// FUNCTION: LEGO1 0x100a66a0
// FUNCTION: BETA10 0x101727c7
void ViewManager::RemoveROIDetailFromScene(ViewROI* p_roi)
{
	assert(p_roi->GetUnknown0xe0() >= 0);
	const ViewLOD* lod = (const ViewLOD*) p_roi->GetLOD(p_roi->GetUnknown0xe0());

	if (lod != NULL) {
		const Tgl::MeshBuilder* meshBuilder = NULL;
		Tgl::Group* roiGeometry = p_roi->GetGeometry();

		meshBuilder = lod->GetMeshBuilder();

		if (meshBuilder != NULL) {
			Tgl::Result result = roiGeometry->Remove(meshBuilder);
			assert(Tgl::Succeeded(result));
		}

		scene->Remove(roiGeometry);
	}

	p_roi->SetUnknown0xe0(-1);
}

// FUNCTION: LEGO1 0x100a66f0
// FUNCTION: BETA10 0x1017297f
inline void ViewManager::ManageVisibilityAndDetailRecursively(ViewROI* p_roi, int p_und)
{
	assert(p_roi);

	if (!p_roi->GetVisibility() && p_und != -2) {
		ManageVisibilityAndDetailRecursively(p_roi, -2);
	}
	else {
		const CompoundObject* comp = p_roi->GetComp();

		if (p_und == -1) {
			if (p_roi->GetWorldBoundingSphere().Radius() > 0.001F) {
				float und = ProjectedSize(p_roi->GetWorldBoundingSphere());

				if (und < seconds_allowed * g_unk0x1010105c) {
					if (p_roi->GetUnknown0xe0() != -2) {
						ManageVisibilityAndDetailRecursively(p_roi, -2);
					}

					return;
				}
				else {
					p_und = CalculateLODLevel(und, RealtimeView::GetUserMaxLodPower() * seconds_allowed, p_roi);
				}
			}
		}

		if (p_und == -2) {
			if (p_roi->GetUnknown0xe0() >= 0) {
				RemoveROIDetailFromScene(p_roi);
				p_roi->SetUnknown0xe0(-2);
			}

			if (comp != NULL) {
				for (CompoundObject::const_iterator it = comp->begin(); it != comp->end(); ++it) {
					ManageVisibilityAndDetailRecursively((ViewROI*) *it, p_und);
				}
			}
			return;
		}

		if (comp == NULL) {
			if (p_roi->GetLODs() != NULL && p_roi->GetLODCount() > 0) {
				UpdateROIDetailBasedOnLOD(p_roi, p_und);
			}

			return;
		}

		p_roi->SetUnknown0xe0(-1);

		for (CompoundObject::const_iterator it = comp->begin(); it != comp->end(); ++it) {
			ManageVisibilityAndDetailRecursively((ViewROI*) *it, p_und);
		}
	}
}

// FUNCTION: LEGO1 0x100a6930
// FUNCTION: BETA10 0x101737ae
void ViewManager::Update(float p_previousRenderTime, float)
{
	MxStopWatch stopWatch;
	stopWatch.Start();

	prev_render_time = p_previousRenderTime;
	flags |= c_bit1;

	if (flags & c_bit3) {
		CalculateFrustumTransformations();
	}
	else if (flags & c_bit2) {
		UpdateViewTransformations();
	}

	for (CompoundObject::iterator it = rois.begin(); it != rois.end(); it++) {
		ManageVisibilityAndDetailRecursively((ViewROI*) *it, -1);
	}

	stopWatch.Stop();
	g_elapsedSeconds = stopWatch.ElapsedSeconds();
}

// FUNCTION: BETA10 0x10174870
inline int ViewManager::CalculateFrustumTransformations()
{
	flags &= ~c_bit3;

	if (height == 0.0F || front == 0.0F) {
		return -1;
	}
	else {
		float fVar7 = tan(view_angle / 2.0F);
		view_area_at_one = view_angle * view_angle * 4.0F;

		float fVar1 = front * fVar7;
		float fVar2 = (width / height) * fVar1;
		float uVar6 = front;
		float fVar3 = back + front;
		float fVar4 = fVar3 / front;
		float fVar5 = fVar4 * fVar1;
		fVar4 = fVar4 * fVar2;

		float* frustumVertices = (float*) this->frustum_vertices;

		// clang-format off
		*frustumVertices = fVar2; frustumVertices++;
		*frustumVertices = fVar1; frustumVertices++;
		*frustumVertices = uVar6; frustumVertices++;
		*frustumVertices = fVar2; frustumVertices++;
		*frustumVertices = -fVar1; frustumVertices++;
		*frustumVertices = uVar6; frustumVertices++;
		*frustumVertices = -fVar2; frustumVertices++;
		*frustumVertices = -fVar1; frustumVertices++;
		*frustumVertices = uVar6; frustumVertices++;
		*frustumVertices = -fVar2; frustumVertices++;
		*frustumVertices = fVar1; frustumVertices++;
		*frustumVertices = uVar6; frustumVertices++;
		*frustumVertices = fVar4; frustumVertices++;
		*frustumVertices = fVar5; frustumVertices++;
		*frustumVertices = fVar3; frustumVertices++;
		*frustumVertices = fVar4; frustumVertices++;
		*frustumVertices = -fVar5; frustumVertices++;
		*frustumVertices = fVar3; frustumVertices++;
		*frustumVertices = -fVar4; frustumVertices++;
		*frustumVertices = -fVar5; frustumVertices++;
		*frustumVertices = fVar3; frustumVertices++;
		*frustumVertices = -fVar4; frustumVertices++;
		*frustumVertices = fVar5; frustumVertices++;
		*frustumVertices = fVar3;
		// clang-format on

		UpdateViewTransformations();
		return 0;
	}
}

// FUNCTION: BETA10 0x10172be5
inline int ViewManager::CalculateLODLevel(float p_und1, float p_und2, ViewROI* p_roi)
{
	assert(p_roi);
	int result;

	if (IsROIVisibleAtLOD(p_roi) != 0) {
		if (p_und1 < g_minLODThreshold) {
			return 0;
		}
		else {
			result = 1;
		}
	}
	else {
		result = 0;
	}

	for (float scale = p_und2; result < g_maxLODLevels; result++) {
		if (scale >= p_und1) {
			break;
		}

		scale *= g_LODScaleFactor;
	}

	return result;
}

// FUNCTION: BETA10 0x10172cb0
inline int ViewManager::IsROIVisibleAtLOD(ViewROI* p_roi)
{
	const LODListBase* lods = p_roi->GetLODs();

	if (lods != NULL && lods->Size() > 0) {
		if (((ViewLOD*) p_roi->GetLOD(0))->GetUnknown0x08Test8()) {
			return 1;
		}
		else {
			return 0;
		}
	}

	const CompoundObject* comp = p_roi->GetComp();

	if (comp != NULL) {
		for (CompoundObject::const_iterator it = comp->begin(); it != comp->end(); it++) {
			const LODListBase* lods = ((ViewROI*) *it)->GetLODs();

			if (lods != NULL && lods->Size() > 0) {
				if (((ViewLOD*) ((ViewROI*) *it)->GetLOD(0))->GetUnknown0x08Test8()) {
					return 1;
				}
				else {
					return 0;
				}
			}
		}
	}

	return 0;
}

// FUNCTION: LEGO1 0x100a6b90
// FUNCTION: BETA10 0x10174610
void ViewManager::UpdateViewTransformations()
{
	flags &= ~c_bit2;

	int i, j, k;

	for (i = 0; i < 8; i++) {
		for (j = 0; j < 3; j++) {
			transformed_points[i][j] = pov[3][j];

			for (k = 0; k < 3; k++) {
				transformed_points[i][j] += pov[k][j] * frustum_vertices[i][k];
			}
		}
	}

	for (i = 0; i < 6; i++) {
		Vector3 a(transformed_points[g_planePointIndexMap[i * 3]]);
		Vector3 b(transformed_points[g_planePointIndexMap[i * 3 + 1]]);
		Vector3 c(transformed_points[g_planePointIndexMap[i * 3 + 2]]);
		Mx3DPointFloat x;
		Mx3DPointFloat y;
		Vector3 normal(frustum_planes[i]);

		x = c;
		x -= b;

		y = a;
		y -= b;

		normal.EqualsCross(x, y);
		if (normal.Unitize()) {
			assert(0);
		}

		frustum_planes[i][3] = -normal.Dot(normal, a);
	}

	flags |= c_bit4;
}

// FUNCTION: LEGO1 0x100a6d50
// FUNCTION: BETA10 0x101738ee
void ViewManager::SetResolution(int width, int height)
{
	this->width = width;
	this->height = height;
	flags |= c_bit3;
}

// FUNCTION: LEGO1 0x100a6d70
// FUNCTION: BETA10 0x1017392b
void ViewManager::SetFrustrum(float fov, float front, float back)
{
	view_angle = fov * 3.14159265359 / 180.0;
	this->front = front;
	this->back = back;
	flags |= c_bit3;
}

// FUNCTION: LEGO1 0x100a6da0
// FUNCTION: BETA10 0x10173977
void ViewManager::SetPOVSource(const OrientableROI* point_of_view)
{
	if (point_of_view != NULL) {
		pov = point_of_view->GetLocal2World();
		flags |= c_bit2;
	}
}

// FUNCTION: LEGO1 0x100a6dc0
// FUNCTION: BETA10 0x101739b8
float ViewManager::ProjectedSize(const BoundingSphere& p_bounding_sphere)
{
	// The algorithm projects the radius of bounding sphere onto the perpendicular
	// plane one unit in front of the camera. That value is simply the ratio of the
	// radius to the distance from the camera to the sphere center. The projected size
	// is then the ratio of the area of that projected circle to the view surface area
	// at Z == 1.0.
	//
	double radius = p_bounding_sphere.Radius();
	float sphere_projected_area = 3.14159265359 * (radius * p_bounding_sphere.Radius());
	float square_dist_to_sphere = DISTSQRD3(p_bounding_sphere.Center(), pov[3]);
	return sphere_projected_area / view_area_at_one / square_dist_to_sphere;
	return 0.0; // DECOMP: intentional unreachable code
}

// FUNCTION: LEGO1 0x100a6e00
// FUNCTION: BETA10 0x10173bd0
ViewROI* ViewManager::Pick(Tgl::View* p_view, unsigned long x, unsigned long y)
{
	LPDIRECT3DRMPICKEDARRAY picked = NULL;
	ViewROI* result = NULL;

	assert(p_view);

	TglImpl::ViewImpl* cast = (TglImpl::ViewImpl*) p_view;
	assert(cast);

	IDirect3DRMViewport* v = cast->ImplementationData();
	assert(v);

	if (v->Pick(x, y, &picked) != D3DRM_OK) {
		assert(0);
		return NULL;
	}

	if (picked != NULL) {
		if (picked->GetSize() != 0) {
			LPDIRECT3DRMVISUAL visual;
			LPDIRECT3DRMFRAMEARRAY frameArray;
			D3DRMPICKDESC desc;

			if (picked->GetPick(0, &visual, &frameArray, &desc) != D3DRM_OK) {
				assert(0);
			}
			else {
				if (frameArray != NULL) {
					int size = frameArray->GetSize();

					if (size > 1) {
						for (int i = 1; i < size; i++) {
							LPDIRECT3DRMFRAME frame = NULL;

							if (frameArray->GetElement(i, &frame) == D3DRM_OK) {
								result = (ViewROI*) frame->GetAppData();

								if (result != NULL) {
									frame->Release();
									break;
								}

								frame->Release();
							}
						}
					}

					visual->Release();
					frameArray->Release();
				}
			}
		}

		picked->Release();
	}

	return result;
}

// FUNCTION: BETA10 0x10174570
inline void SetAppData(ViewROI* p_roi, LPD3DRM_APPDATA data)
{
	IDirect3DRMFrame2* f = NULL;

	if (GetFrame(f, p_roi->GetGeometry()) == 0) {
		assert(f);
		if (f->SetAppData(data)) {
			assert(0);
			return;
		}
	}
}

// FUNCTION: BETA10 0x10171f30
inline BOOL GetD3DRM(IDirect3DRM2*& p_d3drm, Tgl::Renderer* p_tglRenderer)
{
	assert(p_tglRenderer);
	TglImpl::RendererImpl* renderer = (TglImpl::RendererImpl*) p_tglRenderer;
	p_d3drm = renderer->ImplementationData();
	return FALSE;
}

// FUNCTION: BETA10 0x10171f82
inline BOOL GetFrame(IDirect3DRMFrame2*& p_f, Tgl::Group* p_group)
{
	assert(p_f && p_group);
	TglImpl::GroupImpl* cast = (TglImpl::GroupImpl*) p_group;
	assert(cast);
	p_f = cast->ImplementationData();
	assert(p_f);
	return FALSE;
}
