#define PATH_MODE

#include "shape_shader_pixel_common"

uniform float uPhaseOffset;
uniform sampler2D sPointPositionalTexture;

in Vertex
{
	VertexAttrs attrs;
} iVert;

out vec4 fragColor;
void main()
{
	TDCheckDiscard();

	vec4 color = iVert.attrs.color;
	color = applyTexture(color, iVert.attrs, iVert.attrs.pathTex);

	TDAlphaTest(color.a);
	fragColor = TDOutputSwizzle(color);
}

