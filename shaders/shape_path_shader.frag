#define PATH_MODE

#include "shape_shader_pixel_common"

in Vertex
{
	VertexAttrs attrs;
} iVert;

out vec4 fragColor;
void main()
{
	TDCheckDiscard();

	vec4 color = iVert.attrs.color;
	if (!iVert.attrs.visible) {
		color = vec4(0.0);
	} else {
		applyTexture(color, iVert.attrs, iVert.attrs.pathTex);
	}

	TDAlphaTest(color.a);
	fragColor = TDOutputSwizzle(color);
}

