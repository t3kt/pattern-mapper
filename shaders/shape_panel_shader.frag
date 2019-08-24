#define PANEL_MODE

#include "shape_shader_pixel_common"
uniform sampler2D sTexture1;
uniform sampler2D sTexture2;

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
		applyTexture(color, iVert.attrs, iVert.attrs.texLayer1, sTexture1, sTexture2);
		applyTexture(color, iVert.attrs, iVert.attrs.texLayer2, sTexture1, sTexture2);
	}

	TDAlphaTest(color.a);
	fragColor = TDOutputSwizzle(color);
}

